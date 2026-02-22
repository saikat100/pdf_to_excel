import pdfplumber
import pandas as pd
import os
import time

def convert_pdf_to_xlsx_optimized(pdf_path, excel_path):
    """
    Converts PDF to Excel using fast raw text extraction and list splitting/anchoring.
    """
    print(f"Starting optimized conversion for {pdf_path}...")
    start_time = time.time()
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    all_rows = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")
            
            for i, page in enumerate(pdf.pages):
                if i % 100 == 0:
                    print(f"Processing page {i+1}/{total_pages}...")
                
                # Raw text extraction is fast
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                for line in lines:
                    # Filter for transaction lines
                    # Key: Starts with expected TRNC codes
                    clean_line = line.strip()
                    if any(clean_line.startswith(code) for code in ["TKTT", "RFND", "CNCN", "ADMA", "ACMA"]):
                        parts = clean_line.split()
                        
                        # We expect at least ~15 parts for a full transaction line
                        # Start fields: TRNC, Number, Date, CPUI, Code, (STAT), FOP, TransAmt, FareAmt ...
                        # End fields: ... COBL, StdRate, StdAmt, SuppRate, SuppAmt, TaxComm, Balance
                        
                        if len(parts) >= 14:
                            try:
                                # Parse from End (Right Anchoring)
                                # These are standard financial columns at the end
                                balance = parts[-1]
                                tax_on_comm = parts[-2]
                                supp_amt = parts[-3]
                                supp_rate = parts[-4]
                                std_amt = parts[-5]
                                std_rate = parts[-6]
                                cobl_amt = parts[-7] # This is the anchor for the "Messy Middle"
                                
                                # Parse from Start
                                trnc = parts[0]
                                number = parts[1]
                                date = parts[2]
                                cpui = parts[3]
                                code = parts[4]
                                
                                # Heuristic for STAT / FOP
                                # If parts[5] is 2 chars (e.g. CA), it's likely FOP. 
                                # If parts[5] is short code and parts[6] is FOP, then STAT is parts[5]
                                # But based on sample: "FVVV I CA" -> CPUI=FVVV, Code=I, FOP=CA. STAT is missing/empty.
                                # Let's assume standardized index until FOP.
                                
                                # Refined logic: Fare Amount (Index 7) vs Trans Amount (Index 6)
                                # If we look at the sample:
                                # TKTT(0) 506...(1) 02FEB(2) FVVV(3) I(4) CA(5) 23,929(6) 20,452(7) ...
                                
                                stat = "" 
                                fop = parts[5] # Default assignment
                                trans_amt = parts[6]
                                fare_amt = parts[7]
                                
                                # Case: STAT exists, shifting everything by 1?
                                # E.g. "... I XX CA ..." -> parts[5]=XX, parts[6]=CA
                                # Check if parts[6] looks like a number (Trans Amt)
                                # "23,929".replace(',','').isdigit() -> True
                                
                                if not trans_amt.replace(',', '').replace('.', '').lstrip('-').isdigit():
                                    # parts[6] is NOT a number -> likely FOP
                                    # Then parts[5] was STAT
                                    stat = parts[5]
                                    fop = parts[6]
                                    trans_amt = parts[7]
                                    fare_amt = parts[8]
                                    tax_start_idx = 9
                                else:
                                    tax_start_idx = 8

                                # Extract Tax/Middle Block
                                # Everything between Fare Amount and COBL
                                # The index of COBL is -7. In positive indexing this is len(parts) - 7
                                cobl_idx = len(parts) - 7
                                
                                tax_details = " ".join(parts[tax_start_idx : cobl_idx])
                                
                                row = {
                                    "TRNC": trnc,
                                    "Number": number,
                                    "Date": date,
                                    "CPUI": cpui,
                                    "Code": code,
                                    "STAT": stat,
                                    "FOP": fop,
                                    "Transaction Amount": trans_amt,
                                    "FARE Amount": fare_amt,
                                    "Tax Details": tax_details,
                                    "COBL Amount": cobl_amt,
                                    "Std Comm Rate": std_rate,
                                    "Std Comm Amt": std_amt,
                                    "Supp Comm Rate": supp_rate,
                                    "Supp Comm Amt": supp_amt,
                                    "Tax on Comm": tax_on_comm,
                                    "Balance Payable": balance
                                }
                                all_rows.append(row)
                                
                            except IndexError:
                                # Skip lines that don't match structure (robustness)
                                continue

        if all_rows:
            print(f"Extracted {len(all_rows)} transaction rows.")
            df = pd.DataFrame(all_rows)
            
            # Numeric conversion
            num_cols = ["Transaction Amount", "FARE Amount", "COBL Amount", "Std Comm Amt", "Supp Comm Amt", "Tax on Comm", "Balance Payable"]
            for col in num_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df.to_excel(excel_path, index=False)
            print(f"Successfully created {excel_path}")
        else:
            print("No data extracted.")

    except Exception as e:
        print(f"Error: {e}")
        
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    convert_pdf_to_xlsx_optimized("myData.PDF", "myData.xlsx")
