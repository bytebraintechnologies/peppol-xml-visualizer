# Peppol XML Visualizer

A robust, high-performance web service to generate beautiful PDFs from Peppol BIS Billing 3.0 XML documents (Invoices and Credit Notes).

Built with **FastAPI**, **SaxonC** (for XSLT 3.0), and **Microsoft Edge** (for headless HTML-to-PDF rendering).

## Features

*   **Fast & Efficient**:
    *   Pre-compiles XSLT stylesheets on startup using `SaxonC` for near-instant transformations (<10ms).
    *   Efficient global caching of Saxon processors.
    *   Thread-safe architecture.
*   **Support for Peppol Documents**:
    *   Invoices (`urn:oasis:names:specification:ubl:schema:xsd:Invoice-2`)
    *   Credit Notes (`urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2`)
*   **Multiple Output Formats**:
    *   **PDF Binary** (Default)
    *   **HTML** via `Accept: text/html` (Ultra-fast, skips PDF conversion)
    *   **JSON** (`{"pdf_base64": "..."}`) via `Accept: application/json`
    *   **XML** (`<pdf_base64>...</pdf_base64>`) via `Accept: application/xml`
*   **Flexible Deployment**:
    *   Dockerized for easy deployment anywhere.
    *   Includes scripts for Azure VM deployment with Caddy reverse proxy for HTTPS.
*   **SEPA QR Code Integration**:
    *   Generates EPC-compliant SEPA QR codes (v002) for instant mobile payments.
    *   Automatically extracts payment details (IBAN, BIC, Amount, Reference) from Peppol XML.
    *   Supports Belgian structured communication (`+++...+++`) mapping.
    *   Localizable instructions and payment disclaimers (EN, FR, NL, DE).
*   **Localized**:
    *   Built-in support for multiple languages (EN, FR, NL, DE).

## Requirements

*   **Python 3.11+**
*   **Microsoft Edge** (Installed on the host/container for rendering)
*   **saxonche** (Python bindings for Saxon-HE C++)

## Installation

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/peppol-xml-visualizer.git
    cd peppol-xml-visualizer
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application**:
    ```bash
    python -m app.main
    ```
    The API will be available at `http://localhost:8000`.

### Docker

1.  **Build the image**:
    ```bash
    docker build -t peppol-visualizer .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8000:8000 peppol-visualizer
    ```

## Usage

### Endpoints

#### `POST /render`
#### `POST /render`
Upload an XML file to convert it.

**Query Parameters**:
*   `lang`: (Optional) Language code (`en`, `fr`, `nl`, `de`). Default: `en`.
*   `watermark`: (Optional) Text to overlay on the center of each page (e.g., `DUPLICATE`).
*   `merge_attachments`: (Optional) Boolean (true/false). Whether to append embedded PDF attachments found in the XML to the output. Default: `false`.


**Curl Example**:
```bash
curl -X POST "http://localhost:8000/render?lang=en&watermark=DUPLICATE" \
     -H "accept: application/pdf" \
     -F "file=@path/to/invoice.xml" --output result.pdf
```

### JSON Response (Base64)
To get the PDF as a Base64 string in JSON format (useful for API integrations), set the `Accept` header to `application/json`.

```bash
curl -X POST "http://localhost:8000/render?lang=en" \
     -H "accept: application/json" \
     -F "file=@path/to/invoice.xml"
```
**Response**:
```json
{
  "pdf_base64": "JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZw..."
}
```

### Response Headers (Performance Metrics)
The API returns custom headers to help you monitor performance:

| Header | Description |
| :--- | :--- |
| `X-Perf-Xslt-Sec` | Time taken for XSLT transformation (seconds) |
| `X-Perf-Pdf-Sec` | Time taken for PDF conversion (seconds, if applicable) |
| `X-Perf-Total-Sec` | Total processing time (seconds) |
| `X-Cache-Hit` | `True` if a pre-compiled XSLT was used from cache |

## Configuration

The application uses environment variables for configuration. Create a `.env` file based on `.env.example`.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | Port to run the server on | `8000` |
| `XSLT_INVOICE` | Path to Invoice XSLT | `assets/styles/stylesheet-invoice.xslt` |
| `XSLT_CREDITNOTE` | Path to CreditNote XSLT | `assets/styles/stylesheet-creditnote.xslt` |
| `EDGE_BIN` | Path to Edge executable | Auto-detected |

## Deployment (Azure)

The `scripts/deploy_to_azure.py` script automates deployment to a Linux VM on Azure using SSH/SCP.

1.  Configure `.env` with your Azure credentials (`AZURE_HOST`, `AZURE_USER`, `AZURE_PASS`).
2.  Run the script:
    ```bash
    python scripts/deploy_to_azure.py
    ```

## Project Structure

```
├── app/
│   ├── api/            # Routes and Controllers
│   ├── core/           # Config and Settings
│   ├── services/       # Business Logic (PDF, Saxon)
│   ├── main.py         # App Entry Point
├── assets/             # XSLT Stylesheets
├── tests/              # Test Scripts
├── test_data/          # Sample Peppol XMLs
├── scripts/            # Deployment Scripts
├── Dockerfile          # Docker Build
├── Caddyfile           # Caddy Reverse Proxy Config
└── requirements.txt    # Python Dependencies
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Credits

Maintained by **Bytebrain Technology Solutions (BTC)**.

*   **Website**: [https://bytebraintechnologies.com/](https://bytebraintechnologies.com/)
*   **Company ID (BE)**: 0746.412.525
*   **Location**: Sint-Joost-ten-Node, Brussels, Belgium

For commercial support or custom integration, please contact us via our website.
