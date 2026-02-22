import pdfplumber
import pandas as pd
import os
import time
import re
import gc

def parse_amount(val):
    if not val: return 0.0
    # Clean value: remove spaces and commas
    cleaned = str(val).strip().replace(',', '')
    if not cleaned: return 0.0
    # Try to find a number at the start
    match = re.match(r'^-?[\d.]+', cleaned)
    if match:
        try: return float(match.group())
        except ValueError: return 0.0
    return 0.0

def convert_pdf_to_xlsx(pdf_path, excel_path):
    print(f"Starting optimized conversion for {pdf_path} (BSP Format V2)...", flush=True)
    start_time = time.time()
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}", flush=True)
        return

    all_rows = []
    
    # Get total page count first
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
    
    print(f"Total pages: {total_pages}", flush=True)
    
    chunk_size = 100
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        print(f"Processing pages {start_page+1} to {end_page}...", flush=True)
        
        with pdfplumber.open(pdf_path) as pdf:
            for p_idx in range(start_page, end_page):
                page = pdf.pages[p_idx]
                text = page.extract_text(layout=True)
                if not text: continue
                
                lines = text.split('\n')
                current_row = None
                
                for line in lines:
                    clean_line = line.strip()
                    if not clean_line: continue
                    
                    # Identify transaction start
                    # Look for code in the first part of the line
                    parts = line.split()
                    if not parts: continue
                    
                    trnc_match = any(parts[0].startswith(code) for code in ["TKTT", "RFND", "CNCN", "ADMA", "ACMA"])
                    
                    if trnc_match and len(parts) >= 12:
                        if current_row: all_rows.append(current_row)
                        
                        # Use split parts with dynamic detection for STAT/FOP
                        # parts[0]: TRNC
                        # parts[1]: Number
                        # parts[2]: Date
                        # parts[3]: CPUI
                        
                        # Heuristic for NR Code vs STAT vs FOP
                        # Usually: [TRNC] [Number] [Date] [CPUI] [NR_Code] [STAT?] [FOP] [TransAmt] [FareAmt] ...
                        # Column 7 (Amount) is the anchor.
                        
                        # Let's find where the amounts start. 
                        # Financial amounts start around index 6 or 7.
                        # We use regex to find the first token with a digit/comma after CPUI
                        amt_idx = 6
                        for i in range(4, len(parts)):
                            if re.search(r'[\d,]{2,}', parts[i]) and ('.' in parts[i] or ',' in parts[i]):
                                amt_idx = i
                                break
                        
                        # NR Code is alwaysparts[4]
                        nr_code = parts[4]
                        
                        # If amt_idx is 6: parts[5] is FOP, STAT is empty
                        # If amt_idx is 7: parts[5] is STAT, parts[6] is FOP
                        if amt_idx == 6:
                            stat = ""
                            fop = parts[5]
                        elif amt_idx == 7:
                            stat = parts[5]
                            fop = parts[6]
                        else:
                            # Fallback
                            stat = ""
                            fop = parts[amt_idx-1] if amt_idx > 5 else ""

                        # Right anchoring for the rest (last 7 are stable)
                        balance = parts[-1]
                        comm = parts[-2]
                        supp_amt = parts[-3]
                        supp_rate = parts[-4]
                        std_amt = parts[-5]
                        std_rate = parts[-6]
                        cobl = parts[-7]
                        
                        # Middle block for taxes (everything between amt_idx+1 and -7)
                        tax_parts = parts[amt_idx + 2 : -7]
                        # TAX is parts[amt_idx+2] if exists, else empty
                        # F&C is the rest of middle parts
                        
                        tax = parts[amt_idx+2] if len(parts) > amt_idx+2 else ""
                        f_c = " ".join(parts[amt_idx+3 : -7])

                        current_row = {
                            "TRNC": parts[0],
                            "Number": parts[1],
                            "Date": parts[2],
                            "CPUI": parts[3],
                            "Code": nr_code, # This is NR Code (Column E)
                            "STAT": stat,
                            "FOP": fop,
                            "Transaction Amount": parse_amount(parts[amt_idx]),
                            "FARE Amount": parse_amount(parts[amt_idx+1]),
                            "TAX": tax, 
                            "F&C": f_c, 
                            "PEN Amount": 0.0, # Will be summed if sub-lines exist
                            "COBL Amount": parse_amount(cobl),
                            "STD Rate": parse_amount(std_rate),
                            "STD Amt": parse_amount(std_amt),
                            "SUPP Rate": parse_amount(supp_rate),
                            "SUPP Amt": parse_amount(supp_amt),
                            "Comm": parse_amount(comm),
                            "Payable": parse_amount(balance)
                        }
                    elif current_row:
                        # Check sub-lines for more taxes
                        # Sub-lines usually look like: "  99 G8" or "  2,871 TS"
                        # We look at tokens. If a token is numeric and followed by 2 chars, it's a tax.
                        m_parts = line.split()
                        if m_parts and len(m_parts) <= 4:
                            # Heuristic: Tax sub-lines are short
                            for i, part in enumerate(m_parts):
                                if re.match(r'[\d,.]+', part) and i+1 < len(m_parts) and len(m_parts[i+1]) == 2:
                                    # This is a tax entry (Value Code)
                                    val = part
                                    code = m_parts[i+1]
                                    if code in ["G8", "TS", "IO", "T2", "P7", "P8", "BD", "UT", "E5", "E7"]:
                                        current_row["TAX"] += f" {val} {code}"
                                    elif code in ["YQ", "F&C"]:
                                        current_row["F&C"] += f" {val} {code}"
                    
                    if "TOTAL" in line and "ISSUES" not in line:
                         if current_row:
                            all_rows.append(current_row)
                            current_row = None
                
                if current_row:
                    all_rows.append(current_row)
                    current_row = None
        gc.collect()

    if all_rows:
        print(f"Extracted {len(all_rows)} transaction rows.", flush=True)
        df = pd.DataFrame(all_rows)
        
        target_cols = [
            "TRNC", "Number", "Date", "CPUI", "Code", "STAT", "FOP", 
            "Transaction Amount", "FARE Amount", "TAX", "F&C", "COBL Amount",
            "STD Rate", "STD Amt", "SUPP Rate", "SUPP Amt", "Comm", "Payable"
        ]
        
        df = df[target_cols]
        
        # Multi-row header to match BSP Format exactly
        header0 = [
            "", "Document", "Issue", "", "NR", "", "", 
            "Transaction", "FARE", "", "Taxes Fees & Charges", "COBL",
            "------STD Comm------", "", "---SUPP Comm---", "", "Tax on", "Balance"
        ]
        header1 = [
            "TRNC", "Number", "Date", "CPUI", "Code", "STAT", "FOP",
            "Amount", "Amount", "TAX", "F&C", "Amount",
            "Rate", "Amt", "Rate", "Amt", "Comm", "Payable"
        ]
        
        data_list = [header0, header1] + df.values.tolist()
        
        pd.DataFrame(data_list).to_excel(excel_path, index=False, header=False)
        print(f"Successfully created {excel_path} with BSP format.", flush=True)
    else:
        print("No data extracted.", flush=True)
        
    print(f"Total time: {time.time() - start_time:.2f} seconds", flush=True)

if __name__ == "__main__":
    convert_pdf_to_xlsx("myData.PDF", "myData.xlsx")
