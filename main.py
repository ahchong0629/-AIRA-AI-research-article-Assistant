from file_extractor import extract_text_from_pdf
from summarizer import summarize_paper

def save_summary(summary, output_path="summary_output.txt"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Summary saved to {output_path}")

def main(pdf_path):
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    print("Sending to LLM for summarization...")
    summary = summarize_paper(text)

    print("\n===== PAPER SUMMARY =====\n")
    print(summary)

    save_summary(summary)  
    return summary

if __name__ == "__main__":
    main("paper.pdf")
