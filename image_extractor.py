import pymupdf
import base64

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=("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"))

def describe_image(image_data):
    prompt = f"""
    You are analyzing the most important figure from a scientific paper.
    
    Below is the text from the same page as this figure:
    {image_data['page_text'][:3000]}
    
    Please provide:
    1. FIGURE CAPTION: Find and quote the exact caption for this figure from the page text above (e.g. "Figure 1: ...")
    2. DESCRIPTION: What does this figure show? (2-3 sentences)
    3. IMPORTANCE: Why is this figure important to the paper's argument? (1-2 sentences)
    
    If no caption is found, write "Caption not found on this page."
    """

    response = client.chat.completions.create(
        model="gpt-4o", 
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

def find_and_describe_key_image(images):
   
    selection_prompt = """
    You are analyzing figures from a scientific paper.
    I will show you all the figures. Your job is to identify which single figure 
    is most central to the paper's main argument or result.
    
    Reply with ONLY a number (e.g. "3") indicating which figure is most important.
    """
    
    
    content = [{"type": "text", "text": selection_prompt}]
    for i, img in enumerate(images):
        content.append({
            "type": "text", 
            "text": f"Figure {i+1} (page {img['page']}):"
        })
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{img['image_ext']};base64,{img['image_b64']}"
            }
        })
    
    selection_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}]
    )
    
   
    chosen_index = int(selection_response.choices[0].message.content.strip()) - 1
    print(f"LLM selected figure {chosen_index + 1} as most important")
   
    key_image = images[chosen_index]
    description = describe_image(key_image)
    
    return {
        "figure_number": chosen_index + 1,
        "page": key_image["page"],
        "analysis": description
    }
