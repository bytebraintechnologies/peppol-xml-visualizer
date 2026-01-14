import os
import shutil
import tempfile
import uuid
import base64
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Header
from fastapi.responses import Response, JSONResponse

from app.services.pdf_service import process_xml_to_pdf, transform_xml_to_html, check_dependencies

router = APIRouter()

@router.post("/render")
async def convert_xml_to_pdf(
    file: UploadFile = File(...), 
    lang: str = Query("en", description="Language code (en, fr, nl, de)"),
    watermark: str = Query(None, description="Watermark text to overlay on the PDF"),
    merge_attachments: bool = Query(False, description="Whether to merge embedded PDF attachments from the XML"),
    accept: str = Header(default="application/pdf")
):
    """
    Accepts an XML file upload, converts it to PDF or HTML, and returns the result.
    Respects Accept: text/html, application/json, or application/xml.
    """
    check_dependencies()

    with tempfile.TemporaryDirectory() as temp_dir:
        xml_path = os.path.join(temp_dir, f"input_{uuid.uuid4()}.xml")
        try:
            with open(xml_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
        # If user only wants HTML, we skip the PDF generation step (which is slow)
        if "text/html" in accept:
            html_path = os.path.join(temp_dir, f"output_{uuid.uuid4()}.html")
            metrics = transform_xml_to_html(xml_path, html_path, lang)
            # Remove large data not meant for headers
            metrics.pop("sepa_qr_b64", None)
            
            with open(html_path, "rb") as f:
                html_bytes = f.read()
            return Response(content=html_bytes, media_type="text/html", headers=metrics)

        # Default: Generate PDF
        pdf_bytes, metrics, qr_code = process_xml_to_pdf(xml_path, temp_dir, lang, watermark=watermark, merge_attachments=merge_attachments)
        
        if "application/json" in accept:
            pdf_b64_str = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_b64 = f"data:application/pdf;base64,{pdf_b64_str}"
            content = {"pdf_base64": pdf_b64}
            if qr_code:
                content["qr_code_base64"] = qr_code
            return JSONResponse(content=content, headers=metrics)
        
        if "application/xml" in accept:
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            qr_tag = f"<qr_code_base64>{qr_code}</qr_code_base64>" if qr_code else ""
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
    <pdf_base64>{pdf_b64}</pdf_base64>
    {qr_tag}
</response>"""
            return Response(content=xml_content, media_type="application/xml", headers=metrics)
            
        return Response(content=pdf_bytes, media_type="application/pdf", headers=metrics)
