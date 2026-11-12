import os
import platform

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app/
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Assets
DEFAULT_XSLT_INVOICE = os.path.join(PROJECT_ROOT, "assets", "styles", "stylesheet-invoice.xslt")
DEFAULT_XSLT_CREDITNOTE = os.path.join(PROJECT_ROOT, "assets", "styles", "stylesheet-creditnote.xslt")

XSLT_INVOICE = os.getenv("XSLT_INVOICE", DEFAULT_XSLT_INVOICE)
XSLT_CREDITNOTE = os.getenv("XSLT_CREDITNOTE", DEFAULT_XSLT_CREDITNOTE)

# Official OpenPeppol BIS Billing 3.0 stylesheet (one file for Invoice + CreditNote).
# Not committed to the repo: fetched at Docker build time or via scripts/fetch_peppol_stylesheet.sh.
# Kept outside assets/ so the docker-compose assets volume mount does not hide it.
DEFAULT_XSLT_PEPPOL = os.path.join(PROJECT_ROOT, "vendor", "peppol", "stylesheet-ubl.xslt")
XSLT_PEPPOL = os.getenv("XSLT_PEPPOL", DEFAULT_XSLT_PEPPOL)

# Rendering styles selectable via the `style` query parameter
STYLE_DEFAULT = "default"
STYLE_PEPPOL = "peppol"
STYLES = {
    STYLE_DEFAULT: "Bytebrain design (EN/FR/NL/DE, SEPA QR code, self-billing support)",
    STYLE_PEPPOL: "Official OpenPeppol BIS Billing 3.0 stylesheet (English only, billing documents only)",
}

# Server
PORT = int(os.getenv("PORT", 8000))

def get_edge_path():
    env_path = os.getenv("EDGE_BIN")
    if env_path and os.path.exists(env_path):
        return env_path
    
    system = platform.system()
    if system == "Windows":
        paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    elif system == "Linux":
        paths = [
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    return "microsoft-edge"

EDGE_PATH = get_edge_path()
