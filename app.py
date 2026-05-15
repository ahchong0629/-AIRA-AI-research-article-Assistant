import gradio as gr
from file_extractor import extract_text_from_pdf
from summarizer import summarize_paper
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



with gr.Blocks(title="AI Research Paper Summarizer") as app:
    gr.Markdown("## AI Research Paper Summarizer")
    gr.Markdown("Upload a PDF and get a structured summary with key figure analysis. This includes motivation, goal, procedure, results and the open question of the article.\n\nThe machine can make mistakes. Please verify beforehand.")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload your paper (PDF)")
    
    submit_btn = gr.Button("Analyze Paper", variant="primary")
    
    output_box = gr.Textbox(label="Paper Summary", lines=30)
    
    
    submit_btn.click(
        fn=process_pdf_with_timer,
        inputs=[pdf_input],
        outputs=[output_box]
    )

app.launch()
