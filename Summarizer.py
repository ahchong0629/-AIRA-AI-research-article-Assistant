from openai import OpenAI

client = OpenAI(api_key="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")  # 先直接写进去，之后我们会改成更安全的方式

def summarize_paper(text):
    prompt = f"""
    You are an academic paper analysis assistant.
    Read the following paper and extract these four sections:

    - MOTIVATION: Why did the authors do this research? What problem does it address?
    - GOAL: What is the specific objective of this paper?
    - HOW (Procedure): What methods or experiments did they use?
    - RESULT: What are the main findings and conclusions?

    Paper content:
    {text[:8000]}

    Output clearly in English with each section labeled by its title.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
