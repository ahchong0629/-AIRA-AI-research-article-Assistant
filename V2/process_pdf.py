import gradio as gr
import time
timer_label = gr.Textbox(label="Processing Time", interactive=False)

from file_extractor import extract_text_from_pdf,split_pdf
from summarizer import summarize_paper,merge_summaries
from image_extractor import extract_images_with_context, find_and_describe_key_image

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
    
