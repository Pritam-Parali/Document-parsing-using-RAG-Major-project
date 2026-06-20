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
    Convert the content into a Mermaid flowchart.

    Rules:
    - Return ONLY Mermaid code.
    - Start with: flowchart TD
    - Use the main topic as the root node.
    - Create child nodes for key features, concepts, modules, or components.
    - Do NOT create Search, Upload, Request, Notify, User, System, or other generic nodes unless they are explicitly mentioned in the content.
    - Do NOT invent information.
    - Use ONLY information from the content.
    - Keep node labels short (1-4 words).
    - Maximum 10 child nodes.
    - Valid Mermaid syntax only.
    - No explanations.
    - No markdown.

    Example:

    Content:
    Python features include Easy to Learn, Easy to Read, Portable, Open Source.

    Output:
    flowchart TD
    A[Python]
    A --> B[Easy to Learn]
    A --> C[Easy to Read]
    A --> D[Portable]
    A --> E[Open Source]

    Content:
    {text}
    """
    


    response = llm.invoke(prompt)
    
    print(response.content)

    return response.content.strip()