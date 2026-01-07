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

from app.core.config import XSLT_INVOICE, XSLT_CREDITNOTE, EDGE_PATH

# Global State
SAXON_PROC = None
XSLT_CACHE = {}
CACHE_LOCK = threading.Lock()

def initialize_saxon():
    """Initializes the Saxon Processor and compiles stylesheets."""
    global SAXON_PROC, XSLT_CACHE
    print("Initializing Saxon Processor...")
    try:
        SAXON_PROC = PySaxonProcessor(license=False)
        xslt30 = SAXON_PROC.new_xslt30_processor()
        
        if os.path.exists(XSLT_INVOICE):
            print(f"Compiling Invoice XSLT: {XSLT_INVOICE}")
            XSLT_CACHE['Invoice'] = xslt30.compile_stylesheet(stylesheet_file=os.path.abspath(XSLT_INVOICE))
            
        if os.path.exists(XSLT_CREDITNOTE):
            print(f"Compiling CreditNote XSLT: {XSLT_CREDITNOTE}")
            XSLT_CACHE['CreditNote'] = xslt30.compile_stylesheet(stylesheet_file=os.path.abspath(XSLT_CREDITNOTE))
            
    except Exception as e:
        print(f"Error initializing Saxon or compiling XSLT: {e}")

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

def transform_xml_to_html(xml_path: str, output_path: str, lang: str = "en") -> dict:
    """
    Performs XSLT transformation only.
    Returns metrics.
    """
    start_xslt = time.time()
    
    if SAXON_PROC is None:
        raise HTTPException(status_code=500, detail="Saxon Processor not initialized.")

    doc_type = get_xml_type(xml_path)
    executable = XSLT_CACHE.get(doc_type) or XSLT_CACHE.get('Invoice')

    if not executable and doc_type == "CreditNote":
        executable = XSLT_CACHE.get('Invoice')

    if not executable:
        raise HTTPException(status_code=500, detail=f"XSLT for {doc_type} is not cached or available.")

    try:
        with CACHE_LOCK:
            executable.set_parameter("lang", SAXON_PROC.make_string_value(lang))
            executable.transform_to_file(source_file=xml_path, output_file=output_path)
            
        if not os.path.exists(output_path):
             raise RuntimeError("Saxon transformation completed but HTML file not found.")

    except Exception as e:
        print(f"XSLT Error: {e}")
        raise HTTPException(status_code=500, detail=f"XSLT transformation failed: {e}")
    
    time_xslt = time.time() - start_xslt
    return {
        "X-Perf-Xslt-Sec": f"{time_xslt:.4f}",
        "X-Cache-Hit": "True"
    }

def process_xml_to_pdf(xml_path: str, temp_dir: str, lang: str = "en") -> tuple[bytes, dict]:
    """
    Transforms XML to PDF.
    Returns (pdf_bytes, metrics_dict).
    """
    unique_id = str(uuid.uuid4())
    html_path = os.path.join(temp_dir, f"{unique_id}.html")
    pdf_path = os.path.join(temp_dir, f"{unique_id}.pdf")
    
    start_total = time.time()
    
    if SAXON_PROC is None:
        raise HTTPException(status_code=500, detail="Saxon Processor not initialized.")

    doc_type = get_xml_type(xml_path)
    executable = XSLT_CACHE.get(doc_type) or XSLT_CACHE.get('Invoice')

    if not executable and doc_type == "CreditNote":
        executable = XSLT_CACHE.get('Invoice')

    if not executable:
        raise HTTPException(status_code=500, detail=f"XSLT for {doc_type} is not cached or available.")

    # 1. XSLT Transformation
    metrics = transform_xml_to_html(xml_path, html_path, lang)
    time_xslt = float(metrics["X-Perf-Xslt-Sec"])

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

    cmd_pdf = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        file_url
    ]
    
    if platform.system() == "Linux":
        cmd_pdf.insert(1, "--no-sandbox")

    try:
        subprocess.run(cmd_pdf, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore')
            print(f"Edge PDF Error: {err_msg}")
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {err_msg}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF file was not created by Edge.")
    
    time_pdf = time.time() - start_pdf
    time_total = time.time() - start_total

    metrics = {
        "X-Perf-Xslt-Sec": f"{time_xslt:.4f}",
        "X-Perf-Pdf-Sec": f"{time_pdf:.4f}",
        "X-Perf-Total-Sec": f"{time_total:.4f}",
        "X-Cache-Hit": "True"
    }

    with open(pdf_path, "rb") as pdf_file:
        return pdf_file.read(), metrics
