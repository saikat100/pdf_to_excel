import pdfplumber

def test_fixed_width_v2(pdf_path):
    print(f"Testing fixed-width extraction v2 on {pdf_path} (Page 2)...")
    
    # REFINED Column Ranges based on visual inspection
    columns = [
        ("TRNC", 0, 8),          # "TKTT" starts at 5
        ("Number", 8, 21),       # "5060..."
        ("Date", 21, 29),        # "02FEB26"
        ("CPUI", 29, 34),        # "FVVV"
        ("Code", 34, 37),        # "I"
        ("STAT", 37, 41),        # Empty?
        ("FOP", 41, 45),         # "CA"
        ("Trans_Amount", 45, 54), # "23,929"
        ("FARE_Amount", 54, 62),  # "20,452"
        ("TAX", 62, 70),          # "138 E7"
        ("FC", 70, 78),           # "369YQ"
        ("PEN", 78, 83),          # "0" ??
        ("COBL_Amount", 83, 91),  # "20,452"
        ("Balance", 116, 125)     # "22,569"
    ]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[1]
            text = page.extract_text(layout=True)
            lines = text.split('\n')
            
            print("Ruler:    0         10        20        30        40        50        60        70        80        90        100       110       120")
            print("Index:    0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456")
            
            for line in lines:
                if any(line.strip().startswith(code) for code in ["TKTT", "RFND", "CNCN"]):
                    print(f"Line:     {line}")
                    row_data = []
                    for name, start, end in columns:
                        val = line[start:end] if len(line) > start else ""
                        row_data.append(f"{name}='{val.strip()}'")
                    print("Parsed:   " + ", ".join(row_data))
                    print("-" * 100)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fixed_width_v2("myData.PDF")
