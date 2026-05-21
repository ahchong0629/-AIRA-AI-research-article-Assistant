#Version1 AIRA
#Author: Weichuang Lee · [@ahchong0629](https://github.com/ahchong0629)
import pymupdf
import base64
import re
import gradio as gr
import os
import io
import time
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

timer_label = gr.Textbox(label="Processing Time", interactive=False)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))) #If you use Jupyter, just replace "os.getenv("OPENAI_API_KEY")" with your api_key
# ===== FILE EXTRACTOR =====
def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    print(f'The document has {len(doc)} pages.')
    all_text = ""
    for page in doc:
        all_text += page.get_text()
    return all_text

# ===== SUMMARIZER =====
def chunk_text(text, chunk_size=3000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

def summarize_chunk(chunk, chunk_num, total_chunks):
    prompt = f"""
    You are analyzing part {chunk_num} of {total_chunks} of a scientific paper.
    Extract any relevant information about:
    - TITLE (only if found in this section)
    - AUTHORS (only if found in this section)
    - MOTIVATION / problem being solved
    - GOAL / objective
    - HOW / methods and procedures
    - RESULT / findings and conclusions
    - QUESTION / what remains unclear
    If a section is not present, write "Not found in this section."
    Paper section: {chunk}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def merge_summaries(chunk_summaries):
    combined = "\n\n---\n\n".join(chunk_summaries)
    prompt = f"""
    Synthesize these partial summaries into one final summary with sections:
    TITLE, AUTHORS, MOTIVATION, GOAL, HOW (Procedure), RESULT, QUESTION
    Remove repetitions. Partial summaries: {combined}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def summarize_paper(text):
    chunks = chunk_text(text)
    print(f"Paper split into {len(chunks)} chunks")
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        chunk_summaries.append(summarize_chunk(chunk, i+1, len(chunks)))
    print("Merging summaries...")
    return merge_summaries(chunk_summaries)

# ===== IMAGE EXTRACTOR =====
def extract_all_captions(full_text):
    pattern = r'(Fig(?:ure|\.)\s*\d+[a-z]?[\.:].*?)(?=Fig(?:ure|\.)\s*\d+|$)'
    matches = re.findall(pattern, full_text, re.IGNORECASE | re.DOTALL)
    return [m.strip()[:300] for m in matches]

def extract_images_with_context(pdf_path):
    doc = pymupdf.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    all_captions = extract_all_captions(full_text)
    num_real_figures = len(all_captions)
    print(f"Found {num_real_figures} real figures via captions")
    
    all_images = [] #Now, I have to colour the figure as a compromised way to get the LLM to learn
    for page_num, page in enumerate(doc):
        mat = pymupdf.Matrix(2, 2) #double the resolution
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image_b64 = base64.b64encode(img_bytes).decode("utf-8")
        all_images.append({
            "page": page_num + 1,
            "image_b64": image_b64,
            "image_ext": "png",
        })
    
    
    results = []
    for i, img in enumerate(all_images[:num_real_figures]):
        img["page_text"] = all_captions[i] if i < len(all_captions) else "Caption not found"
        results.append(img)
    
    print(f"Using {len(results)} images for analysis")
    return results

def convert_to_png_b64(base_image):
    img_data = base_image["image"]
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def describe_image(images, index, caption):
    prompt = f"""
    You are analyzing Figure {index} from a scientific paper.
    Caption: {caption}
    Please provide:
    1. FIGURE CAPTION: Quote the caption above.
    2. DESCRIPTION: What does this figure show? (2-3 sentences)
    3. IMPORTANCE: Why is this figure important? (1-2 sentences)
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {
                "url": f"data:image/{images['image_ext']};base64,{images['image_b64']}"
            }}
        ]}]
    )
    return response.choices[0].message.content

def pick_key_figure(descriptions):
    # Build a summary of all figures
    figures_summary = "\n\n".join([
        f"Figure {i+1}:\n{desc}" 
        for i, desc in enumerate(descriptions)
    ])
    
    prompt = f"""
    You are an expert scientific reviewer. Below are descriptions of all figures in a paper.
    
    {figures_summary}
    
    Identify which single figure is the most central to the paper's main contribution.
    Prioritize figures that show: key experimental results, performance comparisons, or the core methodology.
    
    Reply in this exact format:
    FIGURE: <number>
    REASON: <one sentence explanation>
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheaper for text-only comparison
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()
    print(f"[DEBUG] Picker response: {raw}")
    
    match = re.search(r'FIGURE:\s*(\d+)', raw)
    return int(match.group(1)) - 1 if match else 0  # return index

def find_and_describe_key_image(images):
    descriptions = []
    for i, img in enumerate(images):
        print(f"Describing figure {i+1}/{len(images)}...")
        desc = describe_image(img, i+1, img['page_text'])
        descriptions.append(desc)
        print(f"Figure {i+1}: {desc[:80]}...")
    
    print("Picking key figure...")
    chosen_index = pick_key_figure(descriptions)
    print(f"Selected figure {chosen_index + 1}")
    
    return {
        "figure_number": chosen_index + 1,
        "page": images[chosen_index]["page"],
        "description": descriptions[chosen_index]
    }

# ===== GRADIO APP =====



def process_pdf(pdf_file):
    start_time = time.time()

    if pdf_file is None:
        return "Please upload a PDF file."
    pdf_path = pdf_file.name
    text = extract_text_from_pdf(pdf_path)
    summary = summarize_paper(text)
    images = extract_images_with_context(pdf_path)
    key_image_result = find_and_describe_key_image(images)
    image_section = f"""
===== KEY FIGURE (Figure {key_image_result['figure_number']}, Page {key_image_result['page']}) =====

{key_image_result['description']}
"""
    elapsed = time.time() - start_time
    elap=str(elapsed)
    full_output = summary + "\n\n" + image_section +"\n\n"+"Processing time:" +elap

    
    with open("summary_output.txt", "w", encoding="utf-8") as f:
        f.write(full_output)
    return full_output



with gr.Blocks(title="AI Research Paper Summarizer") as app:
    gr.Markdown("## AI Research Paper Summarizer")
    gr.Markdown("Upload a PDF and get a structured summary with key figure analysis. This includes motivation, goal, procedure, results and the open question of the article.\n\nThe machine can make mistakes. Please verify beforehand.")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload your paper (PDF)")
    
    submit_btn = gr.Button("Analyze Paper", variant="primary")
    
    output_box = gr.Textbox(label="Paper Summary", lines=30)
    
    
    submit_btn.click(
        fn=process_pdf,
        inputs=[pdf_input],
        outputs=[output_box]
    )

app.launch()
