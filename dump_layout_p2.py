import pdfplumber

def dump_page_layout(pdf_path, output_txt):
    print(f"Dumping layout of {pdf_path} (Page 2) to {output_txt}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                print("PDF has only 1 page.")
                return

            page = pdf.pages[1] # Page 2 (index 1)
            text = page.extract_text(layout=True)
            
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(text if text else "NO TEXT FOUND")
                
            print("Done.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_page_layout("myData.PDF", "page2_layout.txt")
