import gradio as gr
from file_extractor import extract_text_from_pdf
from summarizer import summarize_paper
from image_extractor import extract_images_with_context, find_and_describe_key_image


def process_pdf(pdf_file):
    if pdf_file is None:
        return "Please upload a PDF file.", ""
    
    pdf_path = pdf_file.name 
    
    
    text = extract_text_from_pdf(pdf_path)
    summary = summarize_paper(text)
    images = extract_images_with_context(pdf_path)
    key_image_result = find_and_describe_key_image(images)
    
    
    image_section = f"""
    
===== KEY FIGURE (Figure {key_image_result['figure_number']}, Page {key_image_result['page']}) =====

{key_image_result['analysis']}
"""
    
    full_output = summary + image_section
    

    with open("summary_output.txt", "w", encoding="utf-8") as f: #save it to txt
        f.write(full_output)
    
    return full_output

app = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Upload your paper (PDF)"),
    outputs=gr.Textbox(label="Paper Summary", lines=30),
    title="AI Research Paper Summarizer",
    description="Upload a PDF and get a structured summary with key figure analysis."
)

app.launch()
