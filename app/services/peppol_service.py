import xml.etree.ElementTree as ET

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
