import os
import json
from dotenv import load_dotenv
from google import genai
import fitz  # PyMuPDF

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_json(json_path):
    """Extract and filter JSON content. Only keeps transactions with amount > 8000."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Pre-filtering logic: amount > 8000
    filtered_data = []
    
    # Handle the specific structure seen in your bank statement JSON
    if isinstance(data, list):
        for account in data:
            if 'data' in account and 'Transactions' in account['data']:
                txns = account['data']['Transactions'].get('Transaction', [])
                filtered_txns = []
                for txn in txns:
                    try:
                        # Convert amount to float to compare
                        if float(txn.get('amount', 0)) > 8000:
                            filtered_txns.append(txn)
                    except (ValueError, TypeError):
                        continue
                
                # Update the structure with filtered transactions
                account['data']['Transactions']['Transaction'] = filtered_txns
                filtered_data.append(account)
            else:
                filtered_data.append(account)
    else:
        filtered_data = data

    # Convert the filtered JSON object into a string for the prompt
    return json.dumps(filtered_data, indent=2, ensure_ascii=False)

def extract_text_from_file(file_path):
    """Automatically detect file type and extract text."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == '.json':
        return extract_text_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

def extract_companies(text_content):
    try:
        # Updated prompt to match the specific output table format requested
        prompt = """You are a financial analyst. Based on the provided transaction data, extract ALL payday loan and digital lending companies. 
        
        For each match, return a list including the Date, Company Name/Narration, Type (Debit/Credit), and Amount.
        
        Filter strictly for digital lending, payday loans, or NBFC fintech companies (e.g., Lendingplate, Aman Fincap, etc.). 
        Exclude regular salary credits (unless it's a 'Salary Loan') and credit card payments.

        Return the results in a clear format.

        Text Content:
        """ + text_content

        response = client.models.generate_content(
            model="gemini-2.5-flash", # Updated to the latest stable flash model (gemini-3.1-flash-lite-preview)
            contents=prompt
        )
        
        return response.text
        
    except Exception as e:
        print(f"Error processing: {e}")
        return ""

# Main execution
file_path = r"C:\Users\rahul\Downloads\664332_.json"

print(f"Processing file: {file_path}")
text_content = extract_text_from_file(file_path)
print(f"Filtered text length: {len(text_content)} characters")

print("Processing with Gemini...")
result = extract_companies(text_content)

print("\n" + "="*60)
print("EXTRACTED PAYDAY LOAN TRANSACTIONS (>8000):")
print("="*60)
print(result)
