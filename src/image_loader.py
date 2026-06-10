
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

# Load environment variables
load_dotenv()

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Load Groq Llama
groq_api_key = os.getenv("groq_api_key")

llm = ChatGroq(
    groq_api_key=groq_api_key,
    model_name="llama-3.3-70b-versatile"
)


def extract_text_from_image(image_path: str) -> str:
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text


if __name__ == "__main__":

    image_path = r"C:\Users\Lenovo\OneDrive\Pictures\Screenshots\sample.png"

    try:

        # OCR
        text = extract_text_from_image(image_path)

        print("\n===== OCR TEXT =====\n")
        print(text)

        # Send OCR result to Llama
        prompt = f"""
The following text was extracted from a screenshot.

Please:
1. Summarize it.
2. Explain it in simple language.
3. If it is study material, explain the topic.
4. If it is an error message, explain the fix.

Text:
{text}
"""

        response = llm.invoke(prompt)

        print("\n===== AI EXPLANATION =====\n")
        print(response.content)

    except Exception as e:
        print(f"Error: {e}")
