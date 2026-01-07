import requests
import os

url = "http://127.0.0.1:8000/render"
# Path relative to this test script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
xml_file = os.path.join(os.path.dirname(__file__), "..", "test_data", "peppol-sample-invoice.xml")
output_pdf = "api_result.pdf"

if not os.path.exists(xml_file):
    print(f"Error: {xml_file} does not exist.")
    exit(1)

print(f"Sending {xml_file} to {url}...")
try:
    with open(xml_file, "rb") as f:
        files = {"file": (xml_file, f, "text/xml")}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        with open(output_pdf, "wb") as f:
            f.write(response.content)
        print(f"Success! PDF saved to {output_pdf} ({len(response.content)} bytes).")
    else:
        print(f"Failed. Status Code: {response.status_code}")
        print("Response:", response.text)

except Exception as e:
    print(f"An error occurred: {e}")
