import pymupdf
import os
from dotenv import load_dotenv

load_dotenv("env.txt")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) #If you use Jupyter, just replace "os.getenv("OPENAI_API_KEY")" with your api_key

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    print(f'The document has {len(doc)} pages.')
    all_text = ""
    for page in doc:
        all_text += page.get_text()
    return all_text
