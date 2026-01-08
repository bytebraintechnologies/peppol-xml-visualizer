<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:cn="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
    exclude-result-prefixes="cac cbc cn">

    <xsl:output method="html" version="5.0" encoding="UTF-8" indent="yes"/>

    <!-- Language Parameter -->
    <xsl:param name="lang" select="'en'"/>
    <xsl:param name="sepa_qr_b64" select="''"/>

    <!-- Translations Map -->
    <xsl:variable name="i18n">
        <entry key="title">
            <en>Credit Note</en><fr>Note de crédit</fr><nl>Creditnota</nl><de>Gutschrift</de>
        </entry>
        <entry key="number">
            <en>Number</en><fr>Numéro</fr><nl>Nummer</nl><de>Nummer</de>
        </entry>
        <entry key="issue_date">
            <en>Issue Date</en><fr>Date d'émission</fr><nl>Factuurdatum</nl><de>Ausstellungsdatum</de>
        </entry>
         <!-- Credit notes usually don't have DueDate in the same way, but if present -->
        <entry key="due_date">
            <en>Due Date</en><fr>Date d'échéance</fr><nl>Vervaldatum</nl><de>Fälligkeitsdatum</de>
        </entry>
        <entry key="original_invoice">
            <en>Original Invoice</en><fr>Facture d'origine</fr><nl>Originele factuur</nl><de>Originalrechnung</de>
        </entry>
        <entry key="po">
            <en>Purchase Order</en><fr>Bon de commande</fr><nl>Bestelbon</nl><de>Bestellung</de>
        </entry>
        <entry key="delivery_info">
            <en>Delivery information</en><fr>Informations de livraison</fr><nl>Leveringsinformatie</nl><de>Lieferinformationen</de>
        </entry>
        <entry key="delivery_date">
            <en>Delivery date</en><fr>Date de livraison</fr><nl>Leveringsdatum</nl><de>Lieferdatum</de>
        </entry>
        <entry key="sales_ref">
            <en>Sales order reference</en><fr>Référence commande</fr><nl>Verkooporder referentie</nl><de>Auftragsreferenz</de>
        </entry>
        <entry key="buyer_ref">
            <en>Buyer Reference</en><fr>Référence acheteur</fr><nl>Klantreferentie</nl><de>Käuferreferenz</de>
        </entry>
        <entry key="description_col">
            <en>Product or service</en><fr>Description</fr><nl>Omschrijving</nl><de>Beschreibung</de>
        </entry>
        <entry key="quantity_col">
            <en>Quantity</en><fr>Quantité</fr><nl>Hoeveelheid</nl><de>Menge</de>
        </entry>
        <entry key="price_col">
            <en>Unit Price</en><fr>Prix Unitaire</fr><nl>Eenheidsprijs</nl><de>Einzelpreis</de>
        </entry>
        <entry key="total_col">
            <en>Total</en><fr>Total</fr><nl>Totaal</nl><de>Gesamt</de>
        </entry>
        <entry key="subtotal">
            <en>Subtotal</en><fr>Sous-total</fr><nl>Subtotaal</nl><de>Zwischensumme</de>
        </entry>
        <entry key="total_amount">
            <en>Total Amount</en><fr>Montant Total</fr><nl>Totaalbedrag</nl><de>Gesamtbetrag</de>
        </entry>
        <entry key="payment_info">
            <en>Payment Information</en><fr>Informations de paiement</fr><nl>Betalingsinformatie</nl><de>Zahlungsinformationen</de>
        </entry>
        <entry key="remittance">
            <en>Remittance Info</en><fr>Communication</fr><nl>Mededeling</nl><de>Verwendungszweck</de>
        </entry>
        <entry key="account">
            <en>Account (IBAN)</en><fr>Compte (IBAN)</fr><nl>Rekening (IBAN)</nl><de>Konto (IBAN)</de>
        </entry>
        <entry key="bic">
            <en>BIC / SWIFT</en><fr>BIC / SWIFT</fr><nl>BIC / SWIFT</nl><de>BIC / SWIFT</de>
        </entry>
        <entry key="method">
            <en>Payment Method</en><fr>Méthode de paiement</fr><nl>Betalingswijze</nl><de>Zahlungsmethode</de>
        </entry>
        <entry key="vat_info">
            <en>VAT Info</en><fr>Info TVA</fr><nl>BTW Info</nl><de>USt.-Info</de>
        </entry>
        <entry key="vat_id">
            <en>VAT</en><fr>n° TVA</fr><nl>BTW</nl><de>MwSt.</de>
        </entry>
        <entry key="company_id">
            <en>Company ID</en><fr>BCE</fr><nl>KBO</nl><de>U-Nummer</de>
        </entry>
        <entry key="qr_instruction">
            <en>Scan this QR code with your banking app for easy recognition.</en>
            <fr>Scannez ce code QR avec votre application bancaire pour une reconnaissance facile.</fr>
            <nl>Scan deze QR-code met uw bankapp voor eenvoudige herkenning.</nl>
            <de>Scannen Sie diesen QR-Code mit Ihrer Bank-App zur einfachen Erkennung.</de>
        </entry>
        <entry key="qr_disclaimer">
            <en>Please verify payment details and invoice before executing payment.</en>
            <fr>Veuillez vérifier les détails du paiement et la facture avant d'effectuer le paiement.</fr>
            <nl>Controleer de betalingsgegevens en de factuur voordat u de betaling uitvoert.</nl>
            <de>Bitte überprüfen Sie die Zahlungsdetails und die Rechnung, bevor Sie die Zahlung ausführen.</de>
        </entry>
    </xsl:variable>

    <!-- Main Template -->
    <xsl:template match="/">
        <html>
        <head>
            <title>
                <xsl:value-of select="$i18n/entry[@key='title']/*[local-name()=$lang]"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="*:CreditNote/cbc:ID"/>
            </title>
            <style>
                /* Global Defaults */
                * { box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333;
                    line-height: 1.5;
                    margin: 0;
                    padding: 0;
                    background-color: #fff;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                    counter-reset: page;
                }
                @page { 
                    size: A4; 
                    margin: 20mm; 
                }
                .invoice-container {
                    background: #fff;
                    width: 100%;
                }
                h1, h2, h3, h4, h5 { margin: 0; color: #1a2b3c; }
                h1 { font-size: 24pt; text-align: right; margin-bottom: 20px; text-transform: uppercase; }
                .header-section { display: flex; justify-content: space-between; margin-bottom: 40px; }
                .supplier-details { width: 50%; }
                .invoice-details-box {
                    background-color: #f5f7f9 !important;
                    padding: 15px;
                    border-radius: 4px;
                    font-size: 0.9em;
                    width: 100%;
                }
                .kv-table { display: table; width: 100%; border-collapse: collapse; }
                .kv-row { display: table-row; }
                .kv-key { display: table-cell; font-weight: 600; padding: 4px 8px 4px 0; color: #4a5568; }
                .kv-value { display: table-cell; text-align: right; padding: 4px 0; }
                .bold-name { font-weight: bold; font-size: 14pt; margin-bottom: 5px; color: #1a2b3c; }
                .detail-row { margin-bottom: 2px; font-size: 10pt; }
                .section-label { font-weight: 600; color: #1a2b3c; margin-bottom: 10px; font-size: 11pt; }
                .mid-section { display: flex; margin-bottom: 30px; gap: 30px; }
                .customer-col, .delivery-col { flex: 1; }
                .references-section { display: flex; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; page-break-inside: avoid; }
                .ref-item { margin-right: 40px; }
                .ref-label { font-weight: 600; font-size: 0.9em; display: block; color: #4a5568; }
                table.lines-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 10pt; }
                .lines-table th { text-align: left; font-weight: 600; color: #4a5568; border-bottom: 1px solid #e2e8f0; padding: 10px 0; }
                .lines-table td { padding: 12px 0; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
                .lines-table .text-right { text-align: right; }
                .product-id { font-size: 0.85em; color: #718096; margin-top: 2px; }
                .totals-section { display: flex; justify-content: flex-end; margin-bottom: 40px; page-break-inside: avoid; }
                .totals-box { width: 300px; }
                .total-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 10pt; }
                .total-row.final { font-weight: bold; border-top: 1px solid #e2e8f0; margin-top: 5px; padding-top: 10px; font-size: 12pt; }
                .footer-section { margin-top: 40px; font-size: 9pt; color: #4a5568; page-break-inside: avoid; }
                .footer-block { margin-bottom: 12px; }
                .footer-title { font-weight: bold; margin-bottom: 2px; color: #2d3748; }
                @media print {
                    body { background: none; }
                    .invoice-container { width: 100%; margin: 0; padding: 0; box-shadow: none; border: none; }
                    @page { margin: 15mm; } 
                }
            </style>
        </head>
        <body>
            <div class="invoice-container">
                <!-- Header -->
                <div class="header-section">
                    <div class="supplier-details">
                        <xsl:apply-templates select="*:CreditNote/cac:AccountingSupplierParty" mode="supplier"/>
                    </div>
                    <div class="right-col" style="width: 40%; display: flex; flex-direction: column; align-items: flex-end;">
                        <h1><xsl:value-of select="$i18n/entry[@key='title']/*[local-name()=$lang]"/></h1>
                        <div class="invoice-details-box">
                            <div class="kv-table">
                                <div class="kv-row">
                                    <span class="kv-key"><xsl:value-of select="$i18n/entry[@key='number']/*[local-name()=$lang]"/></span>
                                    <span class="kv-value"><xsl:value-of select="*:CreditNote/cbc:ID"/></span>
                                </div>
                                <div class="kv-row">
                                    <span class="kv-key"><xsl:value-of select="$i18n/entry[@key='issue_date']/*[local-name()=$lang]"/></span>
                                    <span class="kv-value"><xsl:value-of select="*:CreditNote/cbc:IssueDate"/></span>
                                </div>
                                <!-- Billing Reference to Invoice -->
                                <xsl:if test="*:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID">
                                    <div class="kv-row">
                                        <span class="kv-key"><xsl:value-of select="$i18n/entry[@key='original_invoice']/*[local-name()=$lang]"/></span>
                                        <span class="kv-value"><xsl:value-of select="*:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID"/></span>
                                    </div>
                                </xsl:if>
                                <xsl:if test="*:CreditNote/cac:OrderReference/cbc:ID">
                                    <div class="kv-row">
                                        <span class="kv-key"><xsl:value-of select="$i18n/entry[@key='po']/*[local-name()=$lang]"/></span>
                                        <span class="kv-value"><xsl:value-of select="*:CreditNote/cac:OrderReference/cbc:ID"/></span>
                                    </div>
                                </xsl:if>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Customer & Delivery -->
                <div class="mid-section">
                    <div class="customer-col">
                        <xsl:apply-templates select="*:CreditNote/cac:AccountingCustomerParty" mode="customer"/>
                    </div>
                </div>

                <!-- References -->
                <div class="references-section">
                    <xsl:if test="*:CreditNote/cac:OrderReference/cbc:SalesOrderID">
                        <div class="ref-item">
                            <span class="ref-label"><xsl:value-of select="$i18n/entry[@key='sales_ref']/*[local-name()=$lang]"/></span>
                            <span class="ref-value"><xsl:value-of select="*:CreditNote/cac:OrderReference/cbc:SalesOrderID"/></span>
                        </div>
                    </xsl:if>
                    <xsl:if test="*:CreditNote/cbc:BuyerReference">
                        <div class="ref-item">
                            <span class="ref-label"><xsl:value-of select="$i18n/entry[@key='buyer_ref']/*[local-name()=$lang]"/></span>
                            <span class="ref-value"><xsl:value-of select="*:CreditNote/cbc:BuyerReference"/></span>
                        </div>
                    </xsl:if>
                </div>

                <!-- Lines -->
                <table class="lines-table">
                    <thead>
                        <tr>
                            <th style="width: 50%"><xsl:value-of select="$i18n/entry[@key='description_col']/*[local-name()=$lang]"/></th>
                            <th class="text-right"><xsl:value-of select="$i18n/entry[@key='quantity_col']/*[local-name()=$lang]"/></th>
                            <th class="text-right"><xsl:value-of select="$i18n/entry[@key='price_col']/*[local-name()=$lang]"/></th>
                            <th class="text-right"><xsl:value-of select="$i18n/entry[@key='total_col']/*[local-name()=$lang]"/></th>
                        </tr>
                    </thead>
                    <tbody>
                        <xsl:apply-templates select="*:CreditNote/cac:CreditNoteLine"/>
                    </tbody>
                </table>

                <!-- Totals -->
                <div class="totals-section">
                    <div class="totals-box">
                        <div class="total-row">
                            <span><xsl:value-of select="$i18n/entry[@key='subtotal']/*[local-name()=$lang]"/></span>
                            <span>
                                <xsl:value-of select="*:CreditNote/cac:LegalMonetaryTotal/cbc:LineExtensionAmount"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="*:CreditNote/cac:LegalMonetaryTotal/cbc:LineExtensionAmount/@currencyID"/>
                            </span>
                        </div>
                        <xsl:for-each select="*:CreditNote/cac:TaxTotal/cac:TaxSubtotal">
                             <div class="total-row">
                                <span><xsl:value-of select="$i18n/entry[@key='vat_id']/*[local-name()=$lang]"/> (<xsl:value-of select="cac:TaxCategory/cbc:Percent"/>%)</span>
                                <span>
                                    <xsl:value-of select="cbc:TaxAmount"/>
                                    <xsl:text> </xsl:text>
                                    <xsl:value-of select="cbc:TaxAmount/@currencyID"/>
                                </span>
                            </div>
                        </xsl:for-each>
                        
                        <div class="total-row final">
                            <span><xsl:value-of select="$i18n/entry[@key='total_amount']/*[local-name()=$lang]"/></span>
                            <span>
                                <xsl:value-of select="*:CreditNote/cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"/>
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="*:CreditNote/cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount/@currencyID"/>
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Footer / Terms -->
                <div class="footer-section">
                    <xsl:if test="*:CreditNote/cac:PaymentTerms/cbc:Note or *:CreditNote/cac:PaymentMeans">
                        <div class="footer-block">
                            <div class="footer-title"><xsl:value-of select="$i18n/entry[@key='payment_info']/*[local-name()=$lang]"/></div>
                            <xsl:if test="*:CreditNote/cac:PaymentTerms/cbc:Note">
                                <div style="margin-bottom: 8px; font-style: italic;">
                                    <xsl:value-of select="*:CreditNote/cac:PaymentTerms/cbc:Note"/>
                                </div>
                            </xsl:if>
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                <xsl:if test="*:CreditNote/cac:PaymentMeans/cbc:PaymentID">
                                    <tr>
                                        <td style="width: 150px; font-weight: 600; padding: 2px 0;"><xsl:value-of select="$i18n/entry[@key='remittance']/*[local-name()=$lang]"/>:</td>
                                        <td><xsl:value-of select="*:CreditNote/cac:PaymentMeans/cbc:PaymentID"/></td>
                                    </tr>
                                </xsl:if>
                                <xsl:if test="*:CreditNote/cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID">
                                    <tr>
                                        <td style="font-weight: 600; padding: 2px 0;"><xsl:value-of select="$i18n/entry[@key='account']/*[local-name()=$lang]"/>:</td>
                                        <td><xsl:value-of select="*:CreditNote/cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID"/></td>
                                    </tr>
                                </xsl:if>
                                <xsl:if test="*:CreditNote/cac:PaymentMeans/cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID">
                                    <tr>
                                        <td style="font-weight: 600; padding: 2px 0;"><xsl:value-of select="$i18n/entry[@key='bic']/*[local-name()=$lang]"/>:</td>
                                        <td><xsl:value-of select="*:CreditNote/cac:PaymentMeans/cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID"/></td>
                                    </tr>
                                </xsl:if>
                                <xsl:if test="*:CreditNote/cac:PaymentMeans/cbc:PaymentMeansCode">
                                    <tr>
                                        <td style="font-weight: 600; padding: 2px 0;"><xsl:value-of select="$i18n/entry[@key='method']/*[local-name()=$lang]"/>:</td>
                                        <td>
                                            <xsl:value-of select="*:CreditNote/cac:PaymentMeans/cbc:PaymentMeansCode/@name"/> 
                                            (<xsl:value-of select="*:CreditNote/cac:PaymentMeans/cbc:PaymentMeansCode"/>)
                                        </td>
                                    </tr>
                                </xsl:if>
                            </table>
                            <xsl:if test="$sepa_qr_b64 != ''">
                                <div style="margin-top: 20px; display: flex; align-items: flex-start; gap: 15px;">
                                    <img src="{$sepa_qr_b64}" style="width: 100px; height: 100px;"/>
                                    <div style="font-size: 0.8em; color: #666; max-width: 200px; line-height: 1.4;">
                                        <xsl:variable name="instr" select="$i18n/entry[@key='qr_instruction']/*[local-name()=$lang]"/>
                                        <xsl:variable name="disc" select="$i18n/entry[@key='qr_disclaimer']/*[local-name()=$lang]"/>
                                        
                                        <div style="margin-bottom: 4px;">
                                            <xsl:value-of select="if ($instr != '') then $instr else 'Scan this QR code with your banking app for easy recognition.'"/>
                                        </div>
                                        <div style="font-weight: 600; font-size: 0.9em; color: #333;">
                                            <xsl:value-of select="if ($disc != '') then $disc else 'Please verify payment details and invoice before executing payment.'"/>
                                        </div>
                                    </div>
                                </div>
                            </xsl:if>
                        </div>
                    </xsl:if>
                     <xsl:for-each select="*:CreditNote/cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReason">
                        <div class="footer-block">
                             <div class="footer-title"><xsl:value-of select="$i18n/entry[@key='vat_info']/*[local-name()=$lang]"/></div>
                             <div><xsl:value-of select="."/></div>
                        </div>
                     </xsl:for-each>
                </div>
            </div>
        </body>
        </html>
    </xsl:template>

    <xsl:template match="cac:AccountingSupplierParty" mode="supplier">
        <div class="bold-name"><xsl:value-of select="cac:Party/cac:PartyName/cbc:Name"/></div>
        <xsl:apply-templates select="cac:Party/cac:PostalAddress"/>
        <div class="detail-row"><xsl:value-of select="$i18n/entry[@key='vat_id']/*[local-name()=$lang]"/>: <xsl:value-of select="cac:Party/cac:PartyTaxScheme/cbc:CompanyID"/></div>
        <div class="detail-row"><xsl:value-of select="$i18n/entry[@key='company_id']/*[local-name()=$lang]"/>: <xsl:value-of select="cac:Party/cac:PartyLegalEntity/cbc:CompanyID"/></div>
        <div class="detail-row"><xsl:value-of select="cac:Party/cac:Contact/cbc:ElectronicMail"/></div>
        <div class="detail-row"><xsl:value-of select="cac:Party/cac:Contact/cbc:Telephone"/></div>
    </xsl:template>

    <xsl:template match="cac:AccountingCustomerParty" mode="customer">
        <div class="section-label"><xsl:value-of select="cac:Party/cac:PartyName/cbc:Name"/></div>
        <xsl:if test="not(cac:Party/cac:PartyName/cbc:Name)">
             <div class="section-label"><xsl:value-of select="cac:Party/cac:PartyLegalEntity/cbc:RegistrationName"/></div>
        </xsl:if>
        <xsl:apply-templates select="cac:Party/cac:PostalAddress"/>
        <div class="detail-row"><xsl:value-of select="$i18n/entry[@key='vat_id']/*[local-name()=$lang]"/>: <xsl:value-of select="cac:Party/cac:PartyTaxScheme/cbc:CompanyID"/></div>
        <div class="detail-row"><xsl:value-of select="cac:Party/cac:Contact/cbc:ElectronicMail"/></div>
    </xsl:template>

    <xsl:template match="cac:PostalAddress">
        <div class="detail-row"><xsl:value-of select="cbc:StreetName"/> <xsl:text> </xsl:text> <xsl:value-of select="cbc:BuildingNumber"/></div>
        <div class="detail-row"><xsl:value-of select="cbc:PostalZone"/> <xsl:text> </xsl:text> <xsl:value-of select="cbc:CityName"/></div>
        <div class="detail-row"><xsl:value-of select="cac:Country/cbc:IdentificationCode"/> - <xsl:value-of select="cac:Country/cbc:Name"/></div>
    </xsl:template>
    
    <xsl:template match="cac:CreditNoteLine">
        <tr>
            <td>
                <div><xsl:value-of select="cac:Item/cbc:Name"/></div>
                 <xsl:if test="cac:Item/cbc:Description">
                    <div style="font-size: 0.9em; color: #666;"><xsl:value-of select="cac:Item/cbc:Description"/></div>
                </xsl:if>
                 <xsl:if test="cac:Item/cac:SellersItemIdentification/cbc:ID">
                    <div class="product-id">ID: <xsl:value-of select="cac:Item/cac:SellersItemIdentification/cbc:ID"/></div>
                </xsl:if>
            </td>
            <td class="text-right">
                <xsl:value-of select="cbc:CreditedQuantity"/>
                <xsl:text> </xsl:text>
                <span style="font-size: 0.8em; color: #777;"><xsl:value-of select="cbc:CreditedQuantity/@unitCode"/></span>
            </td>
            <td class="text-right">
                <xsl:value-of select="format-number(cac:Price/cbc:PriceAmount, '#.00')"/> 
                <xsl:text> </xsl:text>
                <xsl:value-of select="cac:Price/cbc:PriceAmount/@currencyID"/>
            </td>
            <td class="text-right">
                <xsl:value-of select="format-number(cbc:LineExtensionAmount, '#.00')"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="cbc:LineExtensionAmount/@currencyID"/>
             </td>
        </tr>
    </xsl:template>
</xsl:stylesheet>
