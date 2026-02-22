import pdfplumber

def inspect_page_layout(pdf_path):
    print(f"Inspecting layout of {pdf_path}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            print("\n--- Full Text Layout (Page 1) ---")
            text = page.extract_text(layout=True) # use layout=True to preserve spacing
            print(text)
            
            print("\n--- Table Settings Experiment ---")
            # Try a strategy for tables with horizontal lines but no vertical lines
            settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "lines", 
                "intersection_y_tolerance": 5,
            }
            tables = page.extract_tables(settings)
            print(f"Found {len(tables)} tables with 'text' vertical + 'lines' horizontal strategy.")
            if tables:
                for row in tables[0][:3]:
                     print(row)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_page_layout("myData.PDF")
