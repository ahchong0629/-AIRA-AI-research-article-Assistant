from file_extractor import extract_text_from_pdf
from summarizer import summarize_paper
from image_extractor import extract_images_with_context, find_and_describe_key_image

def save_summary(summary, output_path="summary_output.txt"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Summary saved to {output_path}")

def main(pdf_path):
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    print("Sending to LLM for summarization...")
    summary = summarize_paper(text)

    print("Analyzing key figure...")
    images = extract_images_with_context(pdf_path)
    key_image_result = find_and_describe_key_image(images)
    
    image_section = f"""
===== KEY FIGURE (Figure {key_image_result['figure_number']}, Page {key_image_result['page']}) =====

{key_image_result['analysis']}
"""

    full_output = summary + "\n\n" + image_section

    print("\n===== PAPER SUMMARY =====\n")
    print(full_output)

    save_summary(full_output)
    return full_output

if __name__ == "__main__":
    main("paper.pdf")
