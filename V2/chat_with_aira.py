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
   

