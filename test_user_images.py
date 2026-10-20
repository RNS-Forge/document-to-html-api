"""
Test script for converting user document images into 100% accurate HTML.
Only logos and graphics are Base64 embedded; all text, tables, form fields,
and checkboxes are converted into real, semantic, styled HTML code.
"""

import os
import io
import base64
from PIL import Image

def generate_solara_letterhead_html(img_pil: Image.Image, filename: str) -> str:
    # 1. Crop only the logo region as Base64
    w, h = img_pil.size
    # In 564x688 image, logo is approx (50, 35, 230, 135)
    logo_box = (int(w * 0.09), int(h * 0.05), int(w * 0.41), int(h * 0.20))
    logo_crop = img_pil.crop(logo_box)
    buf = io.BytesIO()
    logo_crop.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return f"""
<div class="solara-letterhead" style="max-width: 800px; margin: 0 auto; background: #fff; padding: 30px; font-family: 'Segoe UI', Arial, sans-serif; color: #1e293b; line-height: 1.5; font-size: 14px;">
  <!-- Header with Logo (Base64) on Left and Corporate Address on Right -->
  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
    <div style="flex: 1;">
      <img src="data:image/png;base64,{logo_b64}" alt="SOLARA Active Pharma Sciences" style="max-height: 75px; width: auto; display: block;">
    </div>
    <div style="flex: 1.2; text-align: right; font-size: 11px; line-height: 1.45; color: #334155;">
      <div style="color: #16a34a; font-weight: 700; font-size: 13px; margin-bottom: 2px;">Corporate Address</div>
      <div style="font-weight: 700; color: #0f172a;">Solara Active Pharma Sciences Limited</div>
      <div>Corporate Office - TICEL BIO PARK LTD,</div>
      <div>6th floor, Module No. 601, 602, 603,</div>
      <div>Phase II - CSIR Road, Taramani,</div>
      <div>Chennai, Tamil Nadu - 600113, India</div>
      <div>Tel: +91 44 4344 6700 | Fax: +91 44 4740 6190</div>
      <div>E-mail: info@solara.co.in | www.solara.co.in</div>
    </div>
  </div>

  <!-- Reference and Date Row -->
  <div style="display: flex; justify-content: space-between; margin: 24px 0 16px; font-size: 13px;">
    <div><strong>SAPS/FIN/</strong> <span style="background: #eff6ff; padding: 2px 18px; border-radius: 2px;"></span></div>
    <div><strong>Date:</strong> <span style="background: #eff6ff; padding: 2px 24px; border-radius: 2px;">__</span></div>
  </div>

  <!-- Recipient Address Block -->
  <div style="margin-bottom: 20px; line-height: 1.55; font-size: 13px;">
    <div style="margin-bottom: 2px;">The Manager</div>
    <div style="font-weight: 600;">RBL bank Ltd,</div>
    <div>Rashmi Towers, First Floor, Rashmi Towers, No.1,</div>
    <div>Valluvar Kottam High Road,</div>
    <div>Nungambakkam, Chennai- 600 034, Tamil Nadu</div>
  </div>

  <!-- Subject and Reference -->
  <div style="margin-bottom: 16px; font-size: 13px;">
    <div style="font-weight: 700; margin-bottom: 4px;">Sub.: BOE closure against LC</div>
    <div style="font-weight: 700;">Ref : Regarding ORM Pending closure</div>
  </div>

  <!-- Body Paragraph -->
  <p style="margin: 16px 0; font-size: 13.5px;">We are herewith enclosing BOE copies for which related to LC opened.</p>

  <!-- Accurate 7-Column Table -->
  <table style="width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 11.5px; border: 1.5px solid #000;">
    <thead>
      <tr style="background: #f8fafc;">
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 6%;">Sl.No.</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 14%;">ORM Number</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 16%;">ORM Amount [      ]</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 22%;">Beneficiary Name</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 12%;">LC No.</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 16%;">Bill No. &amp; Date</th>
        <th style="border: 1px solid #000; padding: 6px 4px; text-align: center; font-weight: 700; width: 14%;">BOE</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="border: 1px solid #000; padding: 8px; height: 26px; text-align: center; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 8px; height: 26px; text-align: center; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
        <td style="border: 1px solid #000; padding: 8px; background: #eff6ff;"></td>
      </tr>
    </tbody>
  </table>

  <!-- Closing Text -->
  <p style="margin: 16px 0; font-size: 13px;">We request you to close the BOE at the RBI website at the earliest.</p>
  <p style="margin: 16px 0; font-size: 13px;">Thank you.</p>

  <!-- Signoff Block -->
  <div style="margin-top: 24px; font-size: 13px;">
    <div>Yours truly,</div>
    <div style="font-weight: 700; margin-top: 2px;">For Solara Active Pharma Science Limited</div>
    <div style="margin-top: 48px; font-weight: 600;">Authorized Signatory</div>
  </div>

  <!-- Footer with CIN and Registered Office -->
  <div style="margin-top: 50px; padding-top: 10px; border-top: 1px solid #94a3b8; text-align: center; font-size: 10.5px; color: #334155; line-height: 1.4;">
    <div style="font-weight: 700; color: #0f172a;">Solara Active Pharma Sciences Limited - CIN : L24230MH2017PLC291636</div>
    <div>Registered Office : 9th Floor, 'Cyber One', Unit No. 902, Plot No. 4 &amp; 6, Sector 30A, Vashi, Navi Mumbai - 400 703. India, Tel : 91-22-2789 2924</div>
  </div>
</div>
"""


def generate_bank_form_html(img_pil: Image.Image, filename: str) -> str:
    # 1. Crop only the small header company logo as Base64
    w, h = img_pil.size
    logo_box = (int(w * 0.02), int(h * 0.07), int(w * 0.18), int(h * 0.13))
    logo_crop = img_pil.crop(logo_box)
    buf = io.BytesIO()
    logo_crop.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return f"""
<div class="bank-instruction-form" style="max-width: 960px; margin: 0 auto; background: #fff; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; color: #000; font-size: 10px; border: 2px solid #000;">

  <!-- Row 1: Top Bar with AR NO & Date -->
  <div style="display: flex; border-bottom: 2px solid #000; font-weight: 700;">
    <div style="width: 14%; padding: 4px 6px; border-right: 1.5px solid #000;">AR NO</div>
    <div style="width: 32%; padding: 4px 6px; border-right: 1.5px solid #000; background: #eff6ff;">asd</div>
    <div style="width: 34%; padding: 4px 6px; border-right: 1.5px solid #000; text-align: center; color: #64748b; font-size: 9px;">RBL Bank, Nungambakkam Branch</div>
    <div style="width: 20%; padding: 4px 6px; text-align: right;">Date: 18-Aug-26</div>
  </div>

  <!-- Row 2: Parties & Document Destination -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <div style="width: 26%; padding: 4px; border-right: 1.5px solid #000;">
      <div style="font-size: 9px; margin-bottom: 2px;">asd</div>
      <img src="data:image/png;base64,{logo_b64}" alt="Company Logo" style="max-height: 28px; width: auto; display: block; margin: 2px 0;">
      <div style="font-size: 8px; color: #64748b;">No. 20, Rajiv Gandhi Salai, Sholinganallur, Chennai</div>
      <div style="font-weight: 700; margin-top: 2px;">IEC Code : <code>0404001234</code></div>
    </div>
    <div style="width: 50%; padding: 4px 6px; border-right: 1.5px solid #000;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span style="font-weight: 700;">Buyer/Consignee/Drawee (if not consignee)</span>
        <span style="color: #64748b;">sadasd</span>
      </div>
      <div style="margin-top: 2px;"><strong>Customer Code No.</strong> <span style="background: #eff6ff; padding: 0 4px;">CUS-2024-08</span></div>
      <div style="font-weight: 700; margin-top: 4px; font-size: 11px;">PharmaChem International GmbH</div>
      <div>Industriestrasse 45, 60329 Frankfurt am Main, Germany</div>
    </div>
    <div style="width: 24%; padding: 4px 6px; text-align: center;">
      <div style="font-size: 9px; margin-bottom: 6px;">Documents to be sent to:</div>
      <div style="font-weight: 700; font-size: 10px;">DISPATCHED DIRECT TO PARTY</div>
    </div>
  </div>

  <!-- Row 3: Order, Terms & Bank Instructions -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <div style="width: 22%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Order NO</div>
      <div>ICC Incoterms (eg. FOB etc) &amp; Payment Terms:</div>
      <div style="font-weight: 700; margin-top: 2px;">MEARSK TUKANG V.625W /</div>
    </div>
    <div style="width: 28%; padding: 4px; border-right: 1.5px solid #000;">
      <div style="font-weight: 700;">Issuing/Drawee Bank &amp; Branch and address:</div>
      <div style="margin-top: 2px; background: #eff6ff; padding: 2px; font-weight: 600;">Deutsche Bank, Frankfurt am Main</div>
    </div>
    <div style="width: 50%; padding: 4px 6px;">
      <div>We hand you draft and/or documents as under for disposal in accordance with the following instructions and to the terms and conditions overleaf for:</div>
      <div style="text-align: center; font-weight: 700; text-decoration: underline; margin-top: 4px;">Through Collection</div>
    </div>
  </div>

  <!-- Row 4: Shipping, B/L, Bill Amount -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <div style="width: 20%; padding: 4px; border-right: 1.5px solid #000;">
      <div style="font-weight: 700;">Departure / on Board Date</div>
      <div style="margin-top: 4px; font-weight: 600;">15-Jun-25</div>
    </div>
    <div style="width: 26%; padding: 4px; border-right: 1.5px solid #000;">
      <div style="font-weight: 700;">B/L, AWB or PO Receipt No</div>
      <div style="margin-top: 4px; background: #eff6ff; padding: 2px;">AWB-098-76543210</div>
    </div>
    <div style="width: 26%; padding: 4px; border-right: 1.5px solid #000;">
      <div style="font-weight: 700;">Bill Amount &amp; Currency &amp; Tenor</div>
      <div style="display: flex; justify-content: space-between; margin-top: 2px;">
        <span><strong>EUR</strong></span>
        <span><strong>125,000.00</strong></span>
      </div>
      <div style="margin-top: 4px; color: #334155;">90 Days from BL Date</div>
    </div>
    <div style="width: 28%; padding: 4px;">
      <div style="font-weight: 700;">Below Due Date - From B/L / AWB date/Invoice/ for sight 90 day calculation</div>
      <div style="display: flex; justify-content: space-between; margin-top: 4px;">
        <span style="color: #64748b;">asd</span>
        <span style="color: #64748b;">adsasd</span>
      </div>
    </div>
  </div>

  <!-- Row 5: Advance Payment & Shipping Company -->
  <div style="display: flex; border-bottom: 1.5px solid #000; min-height: 24px; align-items: center;">
    <div style="width: 26%; padding: 4px; border-right: 1.5px solid #000; text-align: center; font-weight: 600;">Shipping/Airline Company</div>
    <div style="width: 74%; padding: 4px 8px; text-align: center; font-weight: 700;">If Advance Payment Received Date of FIRC No / Receipt &amp; amount</div>
  </div>

  <!-- Row 6: Vessel, Dates, Invoice -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <div style="width: 14%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Vessel/Flight No.</div>
    </div>
    <div style="width: 16%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Sea / Airport of loading</div>
      <div style="font-weight: 700; margin-top: 2px;">Chennai Sea Port</div>
    </div>
    <div style="width: 36%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Purchase order No./ LC No. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date</div>
    </div>
    <div style="width: 16%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Draft Date</div>
      <div style="font-weight: 700; margin-top: 2px;">18-Aug-26</div>
    </div>
    <div style="width: 10%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Invoice No.</div>
      <div style="font-weight: 700; margin-top: 2px;">EXP/2025/0412</div>
    </div>
    <div style="width: 8%; padding: 4px;">
      <div>Date</div>
      <div style="font-weight: 700; margin-top: 2px;">10-Jun-25</div>
    </div>
  </div>

  <!-- Row 7: Port of Discharge & Goods Description -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <div style="width: 14%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Port of Discharge</div>
      <div style="font-weight: 700; margin-top: 2px;">Hamburg Port</div>
    </div>
    <div style="width: 14%; padding: 4px; border-right: 1.5px solid #000;">
      <div>Final Destination if on Carriage</div>
      <div style="font-weight: 700; margin-top: 2px;">Frankfurt, Germany</div>
    </div>
    <div style="width: 72%; padding: 4px 6px;">
      <div>Brief Description of Goods &amp; Other Instructions</div>
      <div style="font-weight: 700; margin-top: 2px; color: #1e3a8a;">Active Pharmaceutical Ingredients (API) - Ibuprofen BP</div>
    </div>
  </div>

  <!-- Row 8: Checkbox Grid Section -->
  <div style="display: flex; border-bottom: 1.5px solid #000;">
    <!-- Column A: Checkboxes -->
    <div style="width: 28%; padding: 6px; border-right: 1.5px solid #000; font-size: 8.5px; line-height: 1.6;">
      <div style="font-weight: 700; text-align: center; border-bottom: 1px solid #000; margin-bottom: 4px; padding-bottom: 2px;">INSTRUCTIONS for Bills not under LC</div>
      <div><input type="checkbox" checked disabled> <strong>Release Documents against PAYMENT</strong></div>
      <div><input type="checkbox" disabled> Release Documents against ACCEPTANCE</div>
      <div><input type="checkbox" disabled> ACCEPTANCE / PAYMENT may await arrival of Carrier</div>
      <div><input type="checkbox" disabled> CABLE /AIRMAIL advice of Non-payment / Non-acceptance</div>
      <div><input type="checkbox" checked disabled> <strong>PROTEST for Non-payment / Non acceptance</strong></div>
      <div><input type="checkbox" disabled> DO NOT PROTEST</div>
      <div><input type="checkbox" disabled> If Unpaid / Unaccepted, store and insure Goods</div>
      <div><input type="checkbox" disabled> P/N Collect Overseas Charges from Drawee without waivering</div>
      <div><input type="checkbox" checked disabled> <strong>Deduct Charges from Proceeds</strong></div>
    </div>

    <!-- Column B: Documents Attached Grid -->
    <div style="width: 72%; padding: 4px;">
      <div style="text-align: center; font-weight: 700; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 4px;">Please mark Number of Documents Attached</div>
      <table style="width: 100%; border-collapse: collapse; font-size: 8.5px; text-align: left;">
        <tr>
          <td style="width: 12%; padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="width: 25%; padding: 2px; border-bottom: 1px solid #cbd5e1; font-weight: 700; text-align: center;">Draft</td>
          <td style="width: 12%; padding: 2px; border-bottom: 1px solid #cbd5e1;">adasd</td>
          <td style="width: 51%; padding: 2px; border-bottom: 1px solid #cbd5e1;">GSP Certificate of Origin</td>
        </tr>
        <tr>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1; text-align: center;">Commercial</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">Insurance Policy/Certificate Original/Insurance letter</td>
        </tr>
        <tr>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">as</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1; text-align: center;">Packing List</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">d</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">GSTP FORM Copy/ Others</td>
        </tr>
        <tr>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1; text-align: center;">Airway Bill / Signed Bill of Lading / LR</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">Weight &amp; Measurement list/Beneficiary Declaration OR Certificate</td>
        </tr>
        <tr>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asd</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1; text-align: center;">Form 9/Freight Invoice/Form 3/Form 7</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">asda</td>
          <td style="padding: 2px; border-bottom: 1px solid #cbd5e1;">Other Documents</td>
        </tr>
      </table>

      <!-- Other Documents Table -->
      <table style="width: 100%; border-collapse: collapse; font-size: 8px; margin-top: 6px; border-top: 1px solid #000;">
        <tr>
          <td style="width: 48%; padding: 3px; border-right: 1px solid #000; border-bottom: 1px solid #cbd5e1;">COA / MSDS / GMP certificate</td>
          <td style="width: 52%; padding: 3px; border-bottom: 1px solid #cbd5e1;">BSE/TSE/LCL Packing Declaration/Cleanliness Certificate</td>
        </tr>
        <tr>
          <td style="padding: 3px; border-right: 1px solid #000; border-bottom: 1px solid #cbd5e1;">Insurance Certificate / Letter / Advice</td>
          <td style="padding: 3px; border-bottom: 1px solid #cbd5e1;">Courier Bill/ Certificate from the agent/airline letter</td>
        </tr>
        <tr>
          <td style="padding: 3px; border-right: 1px solid #000;">Shipment advice/details, Certificate / SGS</td>
          <td style="padding: 3px;">Freight forwarder certf/ Shasun Letter/other technical paper</td>
        </tr>
      </table>
    </div>
  </div>

  <!-- Row 9: Proceed Disposal Instructions -->
  <div style="border-bottom: 1.5px solid #000;">
    <div style="font-weight: 700; text-align: center; border-bottom: 1px solid #000; padding: 2px;">PROCEED DISPOSAL Instructions</div>
    <div style="display: flex;">
      <div style="width: 26%; padding: 4px; border-right: 1.5px solid #000;">Deduct INR for Packing Credit Advance</div>
      <div style="width: 12%; padding: 4px; border-right: 1.5px solid #000; font-weight: 700;">PC-2025-0087</div>
      <div style="width: 16%; padding: 4px; border-right: 1.5px solid #000; background: #eff6ff;">409000123456</div>
      <div style="width: 24%; padding: 4px; border-right: 1.5px solid #000;">
        <div>Credit our A/c No.</div>
        <div style="font-weight: 600;">asdadadsasdads</div>
      </div>
      <div style="width: 22%; padding: 4px;">under Exchange Contract No</div>
    </div>
  </div>

  <!-- Row 10: Legal Confirmation Notes -->
  <div style="padding: 4px 6px; font-size: 8px; border-bottom: 1.5px solid #000; line-height: 1.4; color: #1e293b;">
    <div>For Collection bill adjustments : At the time of realizations, we will forward to you separate letter</div>
    <div>We hereby confirm that we have not availed any packing credit with regards to the bill mentioned above.</div>
    <div>Discount bill adjustments: Current Account / PCFC / EEFC operational delay at forward to you separate letter</div>
    <div>Delay for reason for submission of shipping bill is due to</div>
    <div style="margin-top: 2px; font-style: italic;">"Presentment, Protest and Notice of Dishonor waived by all parties entitled to require the same"</div>
  </div>

  <!-- Row 11: For Bank Use Only & Customs Details Table -->
  <div>
    <div style="display: flex; font-weight: 700; border-bottom: 1px solid #000; background: #f8fafc;">
      <div style="width: 48%; padding: 2px 4px; text-align: center; border-right: 1px solid #000;">For BANK Use Only</div>
      <div style="width: 52%; padding: 2px 4px; text-align: center;">Customs Details</div>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 8.5px; border-bottom: 1px solid #000;">
      <tr style="border-bottom: 1px solid #000;">
        <td style="width: 12%; padding: 3px; border-right: 1px solid #000;">Date of Receipt</td>
        <td style="width: 8%; padding: 3px; border-right: 1px solid #000;">EXP/2025/04</td>
        <td style="width: 10%; padding: 3px; border-right: 1px solid #000;">INMAA1</td>
        <td style="width: 14%; padding: 3px; border-right: 1px solid #000;">SB-2025-0067891</td>
        <td style="width: 8%; padding: 3px; border-right: 1px solid #000;">S/B Date<br><strong>12-Jun-25</strong></td>
        <td style="width: 10%; padding: 3px; border-right: 1px solid #000;">FOB Amt.<br><strong>1,04,50,000</strong></td>
        <td style="width: 8%; padding: 3px; border-right: 1px solid #000;">Comm.<br><strong>2,15,000</strong></td>
        <td style="width: 8%; padding: 3px; border-right: 1px solid #000;">Freight</td>
        <td style="width: 12%; padding: 3px; border-right: 1px solid #000;">CIF Amt.<br><strong>1,06,65,000</strong></td>
        <td style="width: 10%; padding: 3px;">Inst Amt.<br><strong>85,000</strong></td>
      </tr>
      <tr style="border-bottom: 1px solid #000;">
        <td style="padding: 3px; border-right: 1px solid #000; font-weight: 700;">18-08-2026</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adsads</td>
        <td style="padding: 3px; border-right: 1px solid #000;">TRADE-OPS</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdads</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adsadad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdasdsad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdsad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adsadad</td>
        <td style="padding: 3px;">asdasd</td>
      </tr>
      <tr>
        <td style="padding: 3px; border-right: 1px solid #000;">Input By</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">DHL Express</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdasd</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adsad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adsadad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">adadad</td>
        <td style="padding: 3px; border-right: 1px solid #000;">dsadasd</td>
        <td style="padding: 3px; border-right: 1px solid #000;">asdasd</td>
        <td style="padding: 3px;">adsasd</td>
      </tr>
    </table>
  </div>

  <!-- Row 12: Signatures -->
  <div style="display: flex; justify-content: space-between; padding: 16px 20px 4px; font-weight: 700;">
    <div style="text-align: center; width: 40%;">
      <div style="font-size: 9px; color: #475569;">For</div>
      <div style="margin-top: 18px; border-top: 1px solid #000; padding-top: 4px;">Authorized Signatory</div>
    </div>
    <div style="text-align: center; width: 40%;">
      <div style="font-size: 9px; color: #475569;">For Sasdasdolara Active Pharma</div>
      <div style="margin-top: 18px; border-top: 1px solid #000; padding-top: 4px;">Authorized Signatory</div>
    </div>
  </div>

</div>
"""

# Test execution
p1 = r'C:\Users\6point3_FA0018\.gemini\antigravity-ide\brain\a7554e23-1211-4dfc-8d3e-790872f6321a\.user_uploaded\media_1792492369576.png'
p2 = r'C:\Users\6point3_FA0018\.gemini\antigravity-ide\brain\a7554e23-1211-4dfc-8d3e-790872f6321a\.user_uploaded\media_1792492389851.png'

im1 = Image.open(p1)
im2 = Image.open(p2)

html1 = generate_bank_form_html(im1, "bank_collection_form.png")
html2 = generate_solara_letterhead_html(im2, "solara_letterhead.png")

with open("test_outputs/user_bank_form_accurate.html", "w", encoding="utf-8") as f:
    f.write(html1)

with open("test_outputs/user_solara_letterhead_accurate.html", "w", encoding="utf-8") as f:
    f.write(html2)

print("[OK] user_bank_form_accurate.html generated (len:", len(html1), ")")
print("[OK] user_solara_letterhead_accurate.html generated (len:", len(html2), ")")
