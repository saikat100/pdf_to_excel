import pdfplumber
import pandas as pd

def test_fixed_width(pdf_path):
    print(f"Testing fixed-width extraction on {pdf_path} (Page 2)...")
    
    # Column Ranges (guessed from inspection, need tuning)
    # Based on: "   TRNC Number Date  CPUI Code STAT FOP  Amount  Amount TAX    F&C   PEN   Amount Rate Amt Rate  Amt  Comm   Payable"
    columns = [
        ("TRNC", 0, 8),
        ("Number", 8, 20),
        ("Date", 20, 28),
        ("CPUI", 28, 33),
        ("Code", 33, 36), # I space 
        ("STAT", 36, 41), # Space
        ("FOP", 41, 46),  # CA
        ("Trans_Amount", 46, 54),
        ("FARE_Amount", 54, 61),
        ("TAX", 61, 66),      # 138 E7
        ("FC", 66, 74),       # 738 ??
        ("PEN", 74, 80)       # 0
        # ... extending later
    ]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[1]
            text = page.extract_text(layout=True)
            lines = text.split('\n')
            
            extracted = []
            for line in lines:
                # Naive check: if line starts with known codes
                if any(line.strip().startswith(code) for code in ["TKTT", "RFND", "CNCN", "ADMA", "ACMA"]):
                    row = {}
                    for name, start, end in columns:
                        # Safety check for line length
                        val = line[start:end] if len(line) > start else ""
                        row[name] = val.strip()
                    extracted.append(row)
                    print(f"Parsed: {row}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fixed_width("myData.PDF")
