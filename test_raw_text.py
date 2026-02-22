import pdfplumber
import time

def test_raw_text(pdf_path):
    print(f"Testing raw text extraction on {pdf_path} (Page 2)...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            start_time = time.time()
            page = pdf.pages[1]
            text = page.extract_text() # Default (no layout analysis)
            end_time = time.time()
            
            print(f"Extraction took {end_time - start_time:.4f} seconds")
            print("-" * 50)
            print(text[:500]) # Print first 500 chars to check whitespace
            print("-" * 50)
            
            # Check a specific line
            lines = text.split('\n')
            for line in lines:
                if "TKTT" in line:
                    print(f"Sample Line: '{line}'")
                    break

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_text("myData.PDF")
