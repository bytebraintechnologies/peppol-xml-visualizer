import xml.etree.ElementTree as ET
import base64

class PeppolExtractor:
    """Service to extract domain data from Peppol UBL documents."""
    
    @staticmethod
    def extract_sepa_data(xml_path: str) -> dict:
        """Extracts data needed for SEPA QR code using local-name matching."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            def find_val(tag_name):
                for elem in root.iter():
                    if elem.tag.split('}')[-1] == tag_name:
                        return elem.text if elem.text else ""
                return ""

            # Robust search for specific nested structures
            payment_id = ""
            iban = ""
            bic = ""
            
            for pm in root.iter():
                local_tag = pm.tag.split('}')[-1]
                if local_tag == "PaymentMeans":
                    for child in pm.iter():
                        if child.tag.split('}')[-1] == "PaymentID":
                            payment_id = child.text
                            break
                elif local_tag == "PayeeFinancialAccount":
                    for child in pm.iter():
                        if child.tag.split('}')[-1] == "ID":
                            iban = child.text
                            break
                elif local_tag == "FinancialInstitutionBranch":
                    for child in pm.iter():
                        if child.tag.split('}')[-1] == "ID":
                            bic = child.text
                            break

            # Amount extraction
            amount = 0.0
            amount_str = find_val("PayableAmount") or find_val("TaxInclusiveAmount")
            if amount_str:
                try:
                    amount = float(amount_str)
                except ValueError:
                    pass

            # Main Document ID (direct child of root)
            doc_id = ""
            for child in root:
                if child.tag.split('}')[-1] == "ID":
                    doc_id = child.text
                    break
                
            return {
                "name": find_val("RegistrationName") or find_val("Name"),
                "iban": iban,
                "bic": bic,
                "amount": amount,
                "currency": find_val("DocumentCurrencyCode") or "EUR",
                "reference": payment_id,
                "doc_id": doc_id
            }
        except Exception as e:
            print(f"Error extracting SEPA data: {e}")
            return {}

    @staticmethod
    def extract_attachments(xml_path: str) -> list[bytes]:
        """
        Extracts embedded PDF attachments from the XML.
        Looking for:
        cac:AdditionalDocumentReference
          cac:Attachment
            cbc:EmbeddedDocumentBinaryObject mimeCode="application/pdf"
        """
        attachments = []
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Namespace agnostic search or local-name check
            for elem in root.iter():
                if elem.tag.split('}')[-1] == "AdditionalDocumentReference":
                    # Check children for Attachment
                    attachment_node = None
                    for child in elem:
                        if child.tag.split('}')[-1] == "Attachment":
                            attachment_node = child
                            break
                    
                    if attachment_node is not None:
                        # Check for EmbeddedDocumentBinaryObject
                        for bin_obj in attachment_node:
                            if bin_obj.tag.split('}')[-1] == "EmbeddedDocumentBinaryObject":
                                mime = bin_obj.attrib.get("mimeCode", "").lower()
                                if mime == "application/pdf" and bin_obj.text:
                                    try:
                                        # Decode base64
                                        pdf_bytes = base64.b64decode(bin_obj.text.strip())
                                        attachments.append(pdf_bytes)
                                    except Exception as e:
                                        print(f"Failed to decode attachment: {e}")
        except Exception as e:
            print(f"Error extracting attachments: {e}")
            
        return attachments
