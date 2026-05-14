from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chunk_text(text, chunk_size=3000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
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

    If a section is not present in this part, write "Not found in this section."

    Paper section:
    {chunk}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def merge_summaries(chunk_summaries):
    combined = "\n\n---\n\n".join(chunk_summaries)
    merge_prompt = f"""
    Below are partial summaries from different sections of a scientific paper.
    Synthesize into one final summary with these sections:

    - TITLE: Just directly copy and paste the title.
    - Authors: List out all the authors.
    - MOTIVATION: Why did the authors do this research? What problem does it address?
    - GOAL: What is the specific objective of this paper?
    - HOW (Procedure): What methods or experiments did they use?
    - RESULT: What are the main findings and conclusions?
    - QUESTION: What remains unclear in the paper?

    Remove repetitions, keep only the most important information.

    Partial summaries:
    {combined}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": merge_prompt}]
    )
    return response.choices[0].message.content

def summarize_paper(text):
    chunks = chunk_text(text)
    print(f"Paper split into {len(chunks)} chunks")
    
    chunk_summaries = []
    for i, 
