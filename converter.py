import os
import re
import gc
import pypdfium2 as pdfium
import pandas as pd

def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).strip().replace(',', '')
    if not cleaned: return 0.0
    match = re.match(r'^-?[\d.]+', cleaned)
    if match:
        try: return float(match.group())
        except ValueError: return 0.0
    return 0.0

def convert_pdf_to_excel(pdf_path, excel_path):
    """
    Core conversion logic optimized for speed using pypdfium2.
    Prevents 504 Gateway Timeout on hosting providers like PythonAnywhere.
    """
    all_rows = []
    
    pdf = None
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        total_pages = len(pdf)
        
        for i in range(total_pages):
            page = pdf[i]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            if not text: continue
            
            lines = text.split('\n')
            current_row = None
            
            for line in lines:
                parts = line.split()
                if not parts: continue
                
                trnc_match = any(parts[0].startswith(code) for code in ["TKTT", "RFND", "CNCN", "ADMA", "ACMA"])
                
                if trnc_match and len(parts) >= 12:
                    if current_row: all_rows.append(current_row)
                    
                    amt_idx = 6
                    for j in range(4, len(parts)):
                        if re.search(r'[\d,]{2,}', parts[j]) and ('.' in parts[j] or ',' in parts[j]):
                            amt_idx = j
                            break
                    
                    nr_code = parts[4]
                    if amt_idx == 6:
                        stat = ""
                        fop = parts[5]
                    elif amt_idx == 7:
                        stat = parts[5]
                        fop = parts[6]
                    else:
                        stat = ""
                        fop = parts[amt_idx-1] if amt_idx > 5 else ""

                    current_row = {
                        "TRNC": parts[0],
                        "Number": parts[1],
                        "Date": parts[2],
                        "CPUI": parts[3],
                        "Code": nr_code,
                        "STAT": stat,
                        "FOP": fop,
                        "Transaction Amount": parse_amount(parts[amt_idx]),
                        "FARE Amount": parse_amount(parts[amt_idx+1]),
                        "TAX": parts[amt_idx+2] if len(parts) > amt_idx+2 else "", 
                        "F&C": " ".join(parts[amt_idx+3 : -7]), 
                        "COBL Amount": parse_amount(parts[-7]),
                        "STD Rate": parse_amount(parts[-6]),
                        "STD Amt": parse_amount(parts[-5]),
                        "SUPP Rate": parse_amount(parts[-4]),
                        "SUPP Amt": parse_amount(parts[-3]),
                        "Comm": parse_amount(parts[-2]),
                        "Payable": parse_amount(parts[-1])
                    }
                elif current_row:
                    m_parts = line.split()
                    if m_parts and len(m_parts) <= 4:
                        for j, part in enumerate(m_parts):
                            if re.match(r'[\d,.]+', part) and j+1 < len(m_parts) and len(m_parts[j+1]) == 2:
                                val, code = part, m_parts[j+1]
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
            
            # Periodically collect garbage for large files
            if i % 100 == 0:
                gc.collect()
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False
    finally:
        if pdf:
            pdf.close()


    if all_rows:
        df = pd.DataFrame(all_rows)
        target_cols = ["TRNC", "Number", "Date", "CPUI", "Code", "STAT", "FOP", "Transaction Amount", "FARE Amount", "TAX", "F&C", "COBL Amount", "STD Rate", "STD Amt", "SUPP Rate", "SUPP Amt", "Comm", "Payable"]
        df = df[target_cols]
        header0 = ["", "Document", "Issue", "", "NR", "", "", "Transaction", "FARE", "", "Taxes Fees & Charges", "COBL", "------STD Comm------", "", "---SUPP Comm---", "", "Tax on", "Balance"]
        header1 = ["TRNC", "Number", "Date", "CPUI", "Code", "STAT", "FOP", "Amount", "Amount", "TAX", "F&C", "Amount", "Rate", "Amt", "Rate", "Amt", "Comm", "Payable"]
        data_list = [header0, header1] + df.values.tolist()
        pd.DataFrame(data_list).to_excel(excel_path, index=False, header=False)
        return True
    return False

