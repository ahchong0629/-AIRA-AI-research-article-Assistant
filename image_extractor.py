import pymupdf
import base64

def extract_images_with_context(pdf_path):
    doc = pymupdf.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc):
        images = page.get_images()  # 取得这页所有图片
        page_text = page.get_text()  # 取得这页所有文字

        for img_index, img in enumerate(images):
            xref = img[0]  # 图片的唯一 ID
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # 转成 base64，因为 OpenAI API 需要这个格式
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_ext = base_image["ext"]  # jpg, png 等

            results.append({
                "page": page_num + 1,
                "image_b64": image_b64,
                "image_ext": image_ext,
                "page_text": page_text  # 同页文字，用来找 caption
            })

    return results
