import base64
from openai import OpenAI
import os

timer_label = gr.Textbox(label="Processing Time", interactive=False)
load_dotenv("env.txt")
client = OpenAI(api_key=
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
