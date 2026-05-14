import pymupdf
import base64

def extract_images_with_context(pdf_path):
    doc = pymupdf.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc):
        images = page.get_images()  
        page_text = page.get_text()  

        for img_index, img in enumerate(images):
            xref = img[0] 
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
          
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_ext = base_image["ext"]  

            results.append({
                "page": page_num + 1,
                "image_b64": image_b64,
                "image_ext": image_ext,
                "page_text": page_text  
            })

    return results
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def describe_image(image_data):
    prompt = f"""
    You are analyzing a figure from a scientific paper.
    
    Below is the text from the same page as this figure:
    {image_data['page_text'][:3000]}
    
    Please provide:
    1. FIGURE CAPTION: Find and quote the exact caption for this figure from the page text above (e.g. "Figure 1: ...")
    2. DESCRIPTION: What does this figure show? (2-3 sentences)
    3. IMPORTANCE: Why is this figure important to the paper's argument? (1-2 sentences)
    
    If no caption is found, write "Caption not found on this page."
    """

    response = client.chat.completions.create(
        model="gpt-4o",  # 注意：必须用 gpt-4o，不是 mini，因为需要 vision
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_data['image_ext']};base64,{image_data['image_b64']}"
                    }
                }
            ]
        }]
    )

    return response.choices[0].message.content
