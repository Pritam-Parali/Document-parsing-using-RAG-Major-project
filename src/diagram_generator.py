from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    groq_api_key=os.getenv("groq_api_key"),
    model_name="llama-3.3-70b-versatile"
)

def generate_mermaid(text):

    prompt = f"""
Analyze the content and create a Mermaid flowchart.

Rules:
- Return ONLY Mermaid code.
- Start with: flowchart TD
- If the content is a system or project name, create a high-level diagram.
- If the content is a process, create a workflow.
- If the content is theory, create a concept diagram.
- Keep labels short.
- Use valid Mermaid syntax only.
- No explanations.
- No markdown.

Content:
{text}
"""

    response = llm.invoke(prompt)

    return response.content.strip()