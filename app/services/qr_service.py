import qrcode
import io
import base64
from typing import Optional

class SepaQrService:
    """Service for generating EPC-compliant SEPA QR codes."""

    @staticmethod
    def generate_base64(
        name: str,
        iban: str,
        amount: float,
        currency: str = "EUR",
        bic: Optional[str] = None,
        reference: Optional[str] = None,
        remittance: Optional[str] = None,
    ) -> str:
        """
        Generates a SEPA QR code as a base64 encoded PNG string.
        Follows EPC QR Code standard v2.0.
        """
        # Remove spaces from IBAN
        iban = (iban or "").replace(" ", "")
        
        # Format amount with 2 decimal places
        formatted_amount = f"{amount:.2f}"
        amount_with_currency = f"{currency}{formatted_amount}"
        
        lines = [
            "BCD",
            "002",             # Version 2
            "1",               # UTF-8
            "SCT",             # SEPA Credit Transfer
            bic or "",
            name or "",
            iban,
            amount_with_currency,
            reference or "",
            remittance or ""
        ]
        
        qr_content = "\n".join(lines)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return f"data:image/png;base64,{img_str}"

    @classmethod
    def generate_from_peppol_data(cls, doc_type: str, data: dict) -> str:
        """Helper to map Peppol data to SEPA QR fields based on EPC rules."""
        if not data.get("iban") or not data.get("amount") or data.get("amount") <= 0:
            return ""

        raw_ref = data.get("reference", "")
        doc_id = data.get("doc_id", "")
        
        reference = ""
        remittance = ""
        
        # EPC Rule: Structured Reference field is ONLY for ISO 11649 (starts with RF)
        if raw_ref.upper().startswith("RF"):
            reference = raw_ref
        elif raw_ref:
            # Belgian structured comm or other local formats go to Unstructured Remittance
            remittance = raw_ref
        else:
            # Default to document identification
            remittance = f"{'Invoice' if doc_type == 'Invoice' else 'Credit Note'} {doc_id}"

        return cls.generate_base64(
            name=data.get("name", ""),
            iban=data.get("iban", ""),
            amount=data.get("amount", 0.0),
            currency=data.get("currency", "EUR"),
            bic=data.get("bic"),
            reference=reference,
            remittance=remittance
        )
