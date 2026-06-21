from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    groq_api_key=os.getenv("groq_api_key"),
    model_name="llama-3.3-70b-versatile"
)


def summarize_chunk(chunk):

    prompt = f"""
    Summarize this transcript chunk.

    Transcript:
    {chunk}
    """

    return llm.invoke(prompt).content


def generate_final_notes(chunk_summaries):

    merged = "\n\n".join(chunk_summaries)

    prompt = f"""
    Create detailed study notes.

    Format:

    Title

    Introduction

    Key Concepts

    Important Points

    Examples

    Interview Questions

    Summary

    Content:

    {merged}
    """

    return llm.invoke(prompt).content