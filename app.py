import gradio as gr
from file_extractor import extract_text_from_pdf
from summarizer import summarize_paper

def process_pdf(pdf_file):
    if pdf_file is None:
        return "Please upload a PDF file."
    
    text = extract_text_from_pdf(pdf_file.name)
    summary = summarize_paper(text)
    
    # 同时保存 txt
    with open("summary_output.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    
    return summary

app = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Upload your paper (PDF)"),
    outputs=gr.Textbox(label="Paper Summary", lines=20),
    title="AI Research Paper Summarizer",
    description="Upload a PDF and get a structured summary: Motivation, Goal, How, and Result."
)

app.launch()
