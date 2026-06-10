
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

        # Ask user what they want to know
        user_question = input(
            "\nWhat would you like to know about this screenshot?\n> "
        )

        # Send OCR text + question to Llama
        prompt = f"""
You are an AI assistant.

The following text was extracted from a screenshot using OCR.

Screenshot Text:
{text}

User Question:
{user_question}

Instructions:
1. Answer the user's question using the screenshot text.
2. If it is study material, explain it clearly.
3. If it is an error message, explain the cause and solution.
4. If the user asks for notes, create notes.
5. If the user asks for viva questions, create viva questions.
6. If the user asks for a summary, summarize it.

Answer:
"""

        response = llm.invoke(prompt)

        print("\n===== AI RESPONSE =====\n")
        print(response.content)

    except Exception as e:
        print(f"Error: {e}")