import pymupdf
import base64
import re
import gradio as gr
from openai import OpenAI
import os
from dotenv import load_dotenv
from PIL import Image
import io
import time
timer_label = gr.Textbox(label="Processing Time", interactive=False)
load_dotenv("env.txt")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) #If you use Jupyter, just replace "os.getenv("OPENAI_API_KEY")" with your api_key

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
        model="gpt-5.4-mini",
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
        model="gpt-5.4-mini",
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
        model="gpt-5.4",
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
        model="gpt-5.4-mini",  # cheaper for text-only comparison
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


def process_and_chat(pdf_file):
    start_time = time.time()
    
    # step 1 
    chunks = split_pdf(pdf_file)
    yield gr.update(), f"⏱ {time.time() - start_time:.1f}s - Chunking done..."
    
    # step 2
    summary = merge_summaries(chunks)
    yield gr.update(), f"⏱ {time.time() - start_time:.1f}s - Summarizing done..."
    
    # done
    elapsed = time.time() - start_time
    elap=str(elapsed)
    yield final_result

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

def analyze_pdf(pdf_file):  #updated version
    if pdf_file is None:
        return "Please upload a PDF file.", []
    
    pdf_path = pdf_file.name
    
    full_text = extract_text_from_pdf(pdf_path)
    
    summary = process_pdf(pdf_file)
    
   
    images = extract_images_with_context(pdf_path)
    all_figures_desc = "\n".join([
        f"Figure {i+1} (Page {img['page']}): {img['page_text']}"
        for i, img in enumerate(images)
    ])
    
    
    full_context = summary + "\n\n=== ALL FIGURES ===\n" + all_figures_desc
    
    
    initial_message = "I've analyzed the paper! You can ask me about the figures, methodology, or results."
    chat_history = [{"role": "assistant", "content": initial_message}]
    
    
 
    return summary, chat_history, full_context, full_text
    
## Chat with AIRA~~

def chat_with_aira(user_message, chat_history, summary, full_text):  #Chat function!
    if not summary:
        return chat_history + [(user_message, "Please upload a paper first!")], ""
    
    
    messages = [
        {"role": "system", "content": f"""
        You are AIRA, an AI research assistant.
        Here is the FULL TEXT of the paper:
        {full_text}
        You have analyzed this paper and produced the following summary:
        
        {summary}
        
        Answer the user's questions based on this analysis.
        Be specific and reference the paper's content.
        When comparing figures, use ALL the figure descriptions above.
        If a figure is not described, say so explicitly.
        Keep your response concise and accurate, unless the user requests to elaborate.
        """}
    ]
   
    for msg in chat_history[1:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-5.4", 
        messages=messages
    )
    reply = response.choices[0].message.content
    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply}
    ]
    return new_history, ""
   


with gr.Blocks(title="AI Research article Assistant (AIRA)") as app:
    gr.HTML("""
<div style="padding: 16px 0 8px 0;">
    <h1 style="
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, #1a1a2e 00%, #4a2c8a 20%, #7b2ff7 200%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
        margin: 0;
        line-height: 1.1;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    ">AI Research article Assistant (AIRA)</h1>
</div>
""")
    gr.HTML("""
<div style="padding: 4px 0 16px 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <p style="color: #6e6e73; font-size: 14px; margin: 0 0 6px 0; line-height: 1.6;">
        Select a PDF and get a structured summary with key figure analysis locally. 
        This includes motivation, goal, procedure, results and the open question of the article.
    </p>
    
    <p style="color: #6e6e73; font-size: 14px; margin: 0;">
        🔒 Feel Safe. Everything will be carried out locally in your computer, no information will be shared.
    </p>
    <p style="color: #6e6e73; font-size: 10px; margin: 0 0 6px 0;">
        ⚠️ The machine can make mistakes. Please verify beforehand.
    </p>
</div>
""")

    with gr.Row():
        
        with gr.Column(scale=5):
           
            with gr.Group():
                pdf_input = gr.File(label="📄 Select the PDF",height=40)
            submit_btn = gr.Button("Analyze the article locally", variant="primary")
            
            
            chatbot = gr.Chatbot(label="💬 Discuss with AIRA (Chat exists locally, no information will be shared to anyone.)", height=350,elem_id="my_chatbot")
            with gr.Row():
                chat_input = gr.Textbox(placeholder="Ask about the paper...", scale=5)
                send_btn = gr.Button("Send", scale=1)
        
        
        with gr.Column(scale=5):
            output_box = gr.Textbox(label="📋 Paper Summary", lines=22)
    summary_state = gr.State("")
    full_text = gr.State("")
    
    submit_btn.click(
        fn=analyze_pdf,
        inputs=[pdf_input],
        outputs=[output_box, chatbot, summary_state,full_text]
    ).then(
        fn=lambda s: s,  
        inputs=[output_box],
        outputs=[summary_state]
    )

    
    send_btn.click(
        fn=chat_with_aira,
        inputs=[chat_input, chatbot, summary_state,full_text],
        outputs=[chatbot, chat_input]  
    )

    
    chat_input.submit(
        fn=chat_with_aira,
        inputs=[chat_input, chatbot, summary_state,full_text],
        outputs=[chatbot, chat_input]
    )

app.launch(css="""
/* ===== APPLE-STYLE LIGHT THEME ===== */

/* Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* Global */
.gradio-container {
    font-family: -apple-system, 'Inter', BlinkMacSystemFont, sans-serif !important;
    background: #f5f5f7 !important;
    max-width: 100% !important;
}

/* Title */
.gradio-container h1, .gradio-container h2 {
    font-size: 35px !important;
    font-weight: 600 !important;
    color: #1d1d1f !important;
    letter-spacing: -0.5px !important;
}

.gradio-container p {
    color: #6e6e73 !important;
    font-size: 14px !important;
}

/* Buttons */
button.primary {
    background: #0071e3 !important;
    border-radius: 980px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 22px !important;
    border: none !important;
    transition: background 0.2s ease !important;
}
button.primary:hover {
    background: #0077ed !important;
}

/* File upload box */
.upload-container, .file-preview {
    border-radius: 1px !important;
    border: 0px dashed #d2d2d7 !important;
    background: #ffffff !important;
}

/* Chatbot */
.chatbot {
    border-radius: 18px !important;
    border: none !important;
    background: #ffffff !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    font-size: 13px !important;
}

/* Chat messages */
.chatbot .message {
    font-size: 11px !important;
    line-height: 1.5 !important;
    border-radius: 14px !important;
}

/* Chat input */
textarea, input[type="text"] {
    border-radius: 12px !important;
    border: 1.5px solid #d2d2d7 !important;
    background: #ffffff !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #0071e3 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(0,113,227,0.15) !important;
}

/* Summary textbox */
.block.padded {
    background: #ffffff !important;
    border-radius: 18px !important;
    border: none !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
}

/* Labels */
label span {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #6e6e73 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* Send button */
button.secondary {
    border-radius: 980px !important;
    background: #f5f5f7 !important;
    color: #0071e3 !important;
    font-weight: 500 !important;
    border: 1.5px solid #d2d2d7 !important;
    font-size: 13px !important;
}
button.secondary:hover {
    background: #e8e8ed !important;
}
""")
