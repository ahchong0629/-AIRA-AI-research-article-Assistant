import fitz,pymupdf  # PyMuPDF

def extract_text_from_pdf(pdf_path):
  # 打开 PDF，逐页提取文字，合并成一个 string 返回
  doc=pymupdf.open(pdf_path)
  print(f'The document has {len(doc)} pages.')
  all_text=""
  for page in doc:
    text=page.get_text()
    all_text+=text
  return all_text
