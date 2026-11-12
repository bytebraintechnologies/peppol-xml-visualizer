#!/bin/sh
# Downloads the official OpenPeppol BIS Billing 3.0 visualization stylesheet
# (same file as https://docs.peppol.eu/poacc/billing/3.0/files/stylesheet-ubl.xslt),
# pinned to a commit of github.com/OpenPEPPOL/peppol-bis-invoice-3 and verified by checksum.
# It is not committed to this repository because it is published without a license file.
#
# Usage: scripts/fetch_peppol_stylesheet.sh [destination]   (default: vendor/peppol/stylesheet-ubl.xslt)
# To update: change PEPPOL_COMMIT and PEPPOL_SHA256 (sha256sum of the new file).
set -eu

PEPPOL_COMMIT="${PEPPOL_COMMIT:-38d693d71d28d813781323a6ca97324edcc4d239}"
PEPPOL_SHA256="${PEPPOL_SHA256:-2246f758dda011b55bfe4763b3e1677910094e02bef02d2b49fb2f9d29356b27}"
DEST="${1:-$(dirname "$0")/../vendor/peppol/stylesheet-ubl.xslt}"
URL="https://raw.githubusercontent.com/OpenPEPPOL/peppol-bis-invoice-3/${PEPPOL_COMMIT}/stylesheet/stylesheet-ubl.xslt"

mkdir -p "$(dirname "$DEST")"
curl -fsSL "$URL" -o "$DEST.tmp"
echo "${PEPPOL_SHA256}  $DEST.tmp" | sha256sum -c -
mv "$DEST.tmp" "$DEST"
echo "Official Peppol stylesheet saved to $DEST"
