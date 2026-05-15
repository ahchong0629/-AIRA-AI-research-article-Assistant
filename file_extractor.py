import fitz,pymupdf  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    print(f'The document has {len(doc)} pages.')
    all_text = ""
    for page in doc:
        all_text += page.get_text()
    return all_text


