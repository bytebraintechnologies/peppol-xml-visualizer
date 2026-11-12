import os
import uuid
import platform
import subprocess
import threading
import urllib.parse
import time
import traceback
import xml.etree.ElementTree as ET
from saxonche import PySaxonProcessor
from fastapi import HTTPException

from app.services.peppol_service import PeppolExtractor
from app.services.qr_service import SepaQrService
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

from app.core.config import (
    XSLT_INVOICE, XSLT_CREDITNOTE, XSLT_PEPPOL, EDGE_PATH, STYLES, STYLE_DEFAULT, STYLE_PEPPOL
)

# Global State
SAXON_PROC = None
# Compiled stylesheets keyed by (style, document type)
XSLT_CACHE = {}
CACHE_LOCK = threading.Lock()

# The official Peppol stylesheet only renders documents whose CustomizationID starts with this
PEPPOL_BILLING_CUSTOMIZATION = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"

def initialize_saxon():
    """Initializes the Saxon Processor and compiles stylesheets."""
    global SAXON_PROC
    print("Initializing Saxon Processor...")
    try:
        SAXON_PROC = PySaxonProcessor(license=False)
        xslt30 = SAXON_PROC.new_xslt30_processor()
        
    except Exception as e:
        print(f"Error initializing Saxon: {e}")
        return

    def compile_into(style, doc_types, path):
        if not os.path.exists(path):
            print(f"XSLT for style '{style}' not found at {path}; style unavailable.")
            return
        try:
            print(f"Compiling {style} XSLT for {'/'.join(doc_types)}: {path}")
            executable = xslt30.compile_stylesheet(stylesheet_file=os.path.abspath(path))
            for doc_type in doc_types:
                XSLT_CACHE[(style, doc_type)] = executable
        except Exception as e:
            print(f"Error compiling {style} XSLT {path}: {e}")

    compile_into(STYLE_DEFAULT, ["Invoice"], XSLT_INVOICE)
    compile_into(STYLE_DEFAULT, ["CreditNote"], XSLT_CREDITNOTE)
    # The official stylesheet handles both document types in a single file
    compile_into(STYLE_PEPPOL, ["Invoice", "CreditNote"], XSLT_PEPPOL)


def available_styles() -> dict:
    """Returns {style: {"description": ..., "available": bool}}."""
    loaded = {style for style, _ in XSLT_CACHE}
    return {name: {"description": desc, "available": name in loaded} for name, desc in STYLES.items()}

def release_saxon():
    """Releases Saxon resources."""
    global SAXON_PROC
    print("Releasing Saxon Processor...")
    try:
        XSLT_CACHE.clear()
        # In SaxonC-HE 12.x for Python, PySaxonProcessor does not have a .release() method.
        # It is managed by Python's GC or use of 'with' block.
        SAXON_PROC = None
    except Exception as e:
        print(f"Error during Saxon release: {e}")

def check_dependencies():
    if os.path.isabs(EDGE_PATH) and not os.path.exists(EDGE_PATH):
        raise RuntimeError(f"Edge executable not found at '{EDGE_PATH}'.")

def get_xml_type(xml_path: str) -> str:
    """Detects if the XML is an Invoice or CreditNote."""
    try:
        for event, elem in ET.iterparse(xml_path, events=('start',)):
            tag = elem.tag
            if '}' in tag:
                tag = tag.split('}', 1)[1]
            return tag
    except Exception as e:
        print(f"Error checking XML type: {e}")
    return "Invoice"


def get_customization_id(xml_path: str) -> str:
    """Returns the document-level cbc:CustomizationID, or '' if absent."""
    try:
        for child in ET.parse(xml_path).getroot():
            if child.tag.split('}')[-1] == "CustomizationID":
                return (child.text or "").strip()
    except Exception as e:
        print(f"Error reading CustomizationID: {e}")
    return ""


def resolve_executable(style: str, doc_type: str, xml_path: str):
    """Picks the compiled stylesheet for a style/document type, or raises an HTTP error."""
    if style not in STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown style '{style}'. Available styles: {', '.join(STYLES)}."
        )

    if style == STYLE_PEPPOL:
        executable = XSLT_CACHE.get((STYLE_PEPPOL, doc_type))
        if not executable:
            raise HTTPException(
                status_code=503,
                detail="The official Peppol stylesheet is not installed on this server "
                       "(see scripts/fetch_peppol_stylesheet.sh)."
            )
        if not get_customization_id(xml_path).startswith(PEPPOL_BILLING_CUSTOMIZATION):
            raise HTTPException(
                status_code=422,
                detail="The official Peppol stylesheet only supports Peppol BIS Billing 3.0 documents "
                       f"(CustomizationID '{PEPPOL_BILLING_CUSTOMIZATION}'). "
                       "Use style=default for self-billing and other customizations."
            )
        return executable

    executable = XSLT_CACHE.get((STYLE_DEFAULT, doc_type)) or XSLT_CACHE.get((STYLE_DEFAULT, "Invoice"))
    if not executable:
        raise HTTPException(status_code=500, detail=f"XSLT for {doc_type} is not cached or available.")
    return executable


def transform_xml_to_html(xml_path: str, output_path: str, lang: str = "en", style: str = STYLE_DEFAULT) -> dict:
    """
    Performs XSLT transformation only.
    Returns metrics.
    """
    start_xslt = time.time()
    
    if SAXON_PROC is None:
        raise HTTPException(status_code=500, detail="Saxon Processor not initialized.")

    doc_type = get_xml_type(xml_path)
    executable = resolve_executable(style, doc_type, xml_path)

    try:
        lang_code = (lang or "en").lower()
        # Generate SEPA QR if applicable
        sepa_qr_b64 = ""
        # Payment means codes where payment is already handled (no action needed from recipient)
        # 49 = direct debit, 59 = SEPA direct debit (UNCL4461)
        SELF_PAYING_CODES = {"49", "59"}
        if doc_type in ["Invoice", "CreditNote"]:
            data = PeppolExtractor.extract_sepa_data(xml_path)
            if data.get("payment_means_code") in SELF_PAYING_CODES:
                print(f"Skipping SEPA QR: payment means code {data['payment_means_code']} (direct debit)")
            else:
                try:
                    sepa_qr_b64 = SepaQrService.generate_from_peppol_data(doc_type, data)
                    print(f"SEPA QR generated: {len(sepa_qr_b64)} chars")
                except Exception as qr_err:
                    print(f"Warning: Failed to generate SEPA QR: {qr_err}")

        with CACHE_LOCK:
            if style == STYLE_DEFAULT:
                print(f"Setting XSLT parameter 'lang': {lang_code}")
                executable.set_parameter("lang", SAXON_PROC.make_string_value(lang_code))
                executable.set_parameter("sepa_qr_b64", SAXON_PROC.make_string_value(sepa_qr_b64))
            # The official Peppol stylesheet only ships English labels and has no QR slot,
            # so its parameters are left at their defaults.
            executable.transform_to_file(source_file=xml_path, output_file=output_path)
            
        if not os.path.exists(output_path):
             raise RuntimeError("Saxon transformation completed but HTML file not found.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"XSLT Error: {e}")
        raise HTTPException(status_code=500, detail=f"XSLT transformation failed: {e}")
    
    time_xslt = time.time() - start_xslt
    return {
        "X-Perf-Xslt-Sec": f"{time_xslt:.4f}",
        "X-Cache-Hit": "True",
        "X-Style": style,
        "sepa_qr_b64": sepa_qr_b64
    }


def process_xml_to_pdf(xml_path: str, temp_dir: str, lang: str = "en", watermark: str = None, merge_attachments: bool = False,
                       style: str = STYLE_DEFAULT) -> tuple[bytes, dict, str]:
    """
    Transforms XML to PDF.
    Returns (pdf_bytes, metrics_dict, sepa_qr_b64).
    """
    unique_id = str(uuid.uuid4())
    html_path = os.path.join(temp_dir, f"{unique_id}.html")
    pdf_path = os.path.join(temp_dir, f"{unique_id}.pdf")
    
    start_total = time.time()
    
    if SAXON_PROC is None:
        raise HTTPException(status_code=500, detail="Saxon Processor not initialized.")

    doc_type = get_xml_type(xml_path)
    
    # Transform XML to HTML
    metrics = transform_xml_to_html(xml_path, html_path, lang, style=style)
    sepa_qr_b64 = metrics.pop("sepa_qr_b64", "")
    
    # Extract attachments (if any)
    attachments = []
    if merge_attachments:
        attachments = PeppolExtractor.extract_attachments(xml_path)
    
    # 2. PDF Conversion
    start_pdf = time.time()
    abs_html_file_path = os.path.abspath(html_path)
    if platform.system() == "Windows":
        drive, path_part = os.path.splitdrive(abs_html_file_path)
        path_part = path_part.replace('\\', '/')
        path_part = urllib.parse.quote(path_part)
        file_url = f"file:///{drive}{path_part}"
    else:
        file_url = f"file://{abs_html_file_path}"

    # Edge PDF generation - Generate CLEAN pdf with NO header/footer
    # We will add page numbers via post-processing to ensure 100% reliability.
    cmd_parts = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-software-rasterizer",
        "--no-first-run",
        "--no-service-autorun",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-default-apps",
        "--disable-translate",
        "--metrics-recording-only",
        "--safebrowsing-disable-auto-update",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        file_url
    ]
    
    # On Linux, subprocess.run(list) is safer and handles quoting automatically.
    # On Windows, list args also mostly work but we previously had issues with templates.
    # Since we REMOVED the complex templates and are just doing a clean print,
    # list args should work fine everywhere now.

    print(f"Generating clean PDF with command: {cmd_parts}")

    try:
        subprocess.run(cmd_parts, check=True)
        print(f"Clean PDF generated successfully at {pdf_path}")
        
        # Apply page numbering overlay and optional watermark
        post_process_pdf(pdf_path, watermark_text=watermark, attachments=attachments)
        print(f"Post-processing applied to {pdf_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")


    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF file was not created by Edge.")
    
    time_pdf = time.time() - start_pdf
    time_total = time.time() - start_total

    metrics.update({
        "X-Perf-Pdf-Sec": f"{time_pdf:.4f}",
        "X-Perf-Total-Sec": f"{time_total:.4f}",
        "X-Cache-Hit": "True"
    })

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return pdf_bytes, metrics, sepa_qr_b64

def post_process_pdf(pdf_path, watermark_text=None, attachments: list[bytes] = None):
    """
    Overlays page numbers (1 / N) and optional watermark onto the PDF.
    Also merges any attachments found in the XML.
    """
    try:
        # Load main generated PDF
        reader = PdfReader(pdf_path)
        all_pages = []
        all_pages.extend(reader.pages)
        
        # Load and append attachments
        if attachments:
            for att_bytes in attachments:
                try:
                    att_reader = PdfReader(io.BytesIO(att_bytes))
                    all_pages.extend(att_reader.pages)
                except Exception as e:
                    print(f"Skipping invalid attachment: {e}")

        writer = PdfWriter()
        total_pages = len(all_pages)
        
        for i, page in enumerate(all_pages):
            page_number = i + 1
            
            # Create a memory buffer for the overlay (numbering + watermark)
            packet = io.BytesIO()
            # Use A4 size; invoice is usually A4.
            # Note: If attachment is different size, this overlay might be misaligned, 
            # but for now assume A4 or standard behavior.
            can = canvas.Canvas(packet, pagesize=A4)
            
            # 1. Page Numbering
            # Styling: Grey, small font, bottom right
            text = f"{page_number} / {total_pages}"
            can.setFont("Helvetica", 9)
            can.setFillColorRGB(0.6, 0.6, 0.6)
            
            # Position: 20mm from right, 12mm from bottom (footer area)
            text_width = can.stringWidth(text, "Helvetica", 9)
            x_pos = (210 * mm) - (20 * mm) - text_width
            y_pos = 12 * mm
            can.drawString(x_pos, y_pos, text)

            # 2. Optional Watermark
            if watermark_text:
                can.saveState()
                can.translate(105 * mm, 148.5 * mm) # Move to center of A4
                can.rotate(45)
                can.setFont("Helvetica-Bold", 60)
                # Light grey, semi-transparent
                can.setFillColorRGB(0.85, 0.85, 0.85, alpha=0.5)
                # Draw centered
                w_width = can.stringWidth(watermark_text, "Helvetica-Bold", 60)
                can.drawString(-w_width / 2, 0, watermark_text)
                can.restoreState()

            can.save()
            
            packet.seek(0)
            overlay_pdf = PdfReader(packet)
            
            # Merge overlay onto the original page
            # Note: page.merge_page modifies the page object in place
            page.merge_page(overlay_pdf.pages[0])
            writer.add_page(page)
            
        # Write to a temporary file first to avoid corruption (reading/writing same file)
        temp_final_path = pdf_path.replace(".pdf", "_final.pdf")
        with open(temp_final_path, "wb") as f:
            writer.write(f)
            
        # Replace original
        os.replace(temp_final_path, pdf_path)
            
    except Exception as e:
        print(f"Error applying post-processing: {e}")
        traceback.print_exc()
        # Non-fatal: if failing, return the clean (but unmerged) PDF
