import re

def test_regex():
    # Sample line from previous output
    # "TKTT 5060513314 02FEB26 FVVV I CA 23,929 20,452 138 E7 369YQ 20,452 7.00 1,432 0.00 0 -72 22,569"
    # Note: 
    # STAT: Empty?
    # FOP: CA
    # Trans Amt: 23,929
    # FARE Amt: 20,452
    # TAX+F&C+PEN: "138 E7 369YQ"
    # COBL: 20,452
    
    line = "TKTT 5060513314 02FEB26 FVVV I CA 23,929 20,452 138 E7 369YQ 20,452 7.00 1,432 0.00 0 -72 22,569"

    # Pattern:
    # 1. TRNC - 4 chars
    # 2. Number - digits
    # 3. Date - alphanumeric
    # 4. CPUI - alphanumeric
    # 5. Code - 1 char
    # 6. STAT/FOP - Combined 2-4 chars (CA or STAT CA)
    # 7. Amounts - series of numbers/commas
    
    # Let's anchor from the end:
    # Space separated:
    # -1: 22,569 (Balance)
    # -2: -72 (Tax on Comm)
    # -3: 0 (Supp Amt)
    # -4: 0.00 (Supp Rate)
    # -5: 1,432 (Std Amt)
    # -6: 7.00 (Std Rate)
    # -7: 20,452 (COBL)
    
    # Everything before COBL is the "Messy Middle" + Headers
    
    parts = line.split()
    print("Parts:", parts)
    
    # Expected:
    # 0: TKTT
    # 1: 5060...
    # 2: 02FEB26
    # 3: FVVV
    # 4: I
    # 5: CA (FOP)
    # 6: 23,929 (Trans)
    # 7: 20,452 (Fare)
    # 
    # End:
    # ...
    # -7: 20,452 (COBL)
    # Mid: parts[8 : -7] -> ['138', 'E7', '369YQ'] -> TAX Details
    
    cobl_idx = -7 # Based on counting
    
    if len(parts) >= 15: # Safety check
        trnc = parts[0]
        number = parts[1]
        date = parts[2]
        cpui = parts[3]
        code = parts[4]
        stat_fop = parts[5] # Might be just FOP if STAT is empty
        trans_amt = parts[6]
        fare_amt = parts[7]
        
        # Determine dynamic range for Tax
        # Everything between index 7 (fare) and index -7 (cobl)
        tax_details = " ".join(parts[8 : cobl_idx])
        
        cobl = parts[cobl_idx]
        std_rate = parts[cobl_idx + 1]
        std_amt = parts[cobl_idx + 2]
        supp_rate = parts[cobl_idx + 3]
        supp_amt = parts[cobl_idx + 4]
        tax_comm = parts[cobl_idx + 5]
        balance = parts[cobl_idx + 6]
        
        print(f"TRNC: {trnc}")
        print(f"Details: {number} | {date}")
        print(f"Amounts: T={trans_amt}, F={fare_amt}")
        print(f"TAX Details: {tax_details}")
        print(f"COBL: {cobl}")
        print(f"Balance: {balance}")
    else:
        print("Line too short")

if __name__ == "__main__":
    test_regex()
