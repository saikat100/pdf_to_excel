import pdfplumber

def dump_page_layout(pdf_path, output_txt):
    print(f"Dumping layout of {pdf_path} to {output_txt}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            # Use layout=True to attempt to preserve physical layout
            text = page.extract_text(layout=True)
            
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(text if text else "NO TEXT FOUND")
                
            print("Done.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_page_layout("myData.PDF", "page1_layout.txt")
