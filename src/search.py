import os
from dotenv import load_dotenv
from src.vectorestore import FaissVectorStore
from langchain_groq import ChatGroq
import pandas as pd
from src.csv_agent import analyze_csv
from pathlib import Path

load_dotenv()

class RAGSearch:
    def __init__(self,persist_dir:str="faiss_store",embedding_model:str="all-MiniLM-L6-v2",llm_model:str="llama-3.3-70b-versatile"):
        self.vectorstore = FaissVectorStore(persist_dir,embedding_model)
        faiss_path = os.path.join(persist_dir,'faiss.index')
        meta_path = os.path.join(persist_dir,'metadata.pkl')
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            from src.data_loader import load_all_documents
            docs = load_all_documents("data")
            self.vectorstore.build_from_documents(docs)
            self.vectorstore.save()
        else:
            self.vectorstore.load()
        
        groq_api_key = os.getenv("groq_api_key")
        self.llm = ChatGroq(groq_api_key=groq_api_key,model_name = llm_model)
        print(f"Groq LLm initialized : {llm_model}")


    def search_and_summarize(self, query: str, top_k: int = 5) -> str:

        csv_files = list(Path("data").glob("*.csv"))

        for csv_file in csv_files:
            csv_answer = analyze_csv(
                query,
                str(csv_file)
            )
            if csv_answer:
                return csv_answer

        results = self.vectorstore.query(query, top_k=top_k)

        # ---------------- DEBUGGING ---------------- #
        print("\n" + "=" * 100)
        print(f"QUERY: {query}")
        print(f"RETRIEVED {len(results)} RESULTS")
        print("=" * 100)

        for i, r in enumerate(results, start=1):

            print(f"\nRESULT #{i}")

            if r["metadata"]:
                print("SOURCE:", r["metadata"].get("source", "Unknown"))
                print("DISTANCE:", r.get("distance"))

                text = r["metadata"].get("text", "")
                print("TEXT PREVIEW:")
                print(text[:500])

            else:
                print("No metadata found.")

            print("-" * 100)

        # ---------------- CONTEXT EXTRACTION ---------------- #

        texts = [
            r["metadata"].get("text", "")
            for r in results
            if r["metadata"]
        ]

        context = "\n\n".join(texts).strip()

        print("\nCONTEXT SENT TO LLM:")
        print("=" * 100)
        print(context[:3000])
        print("=" * 100)

        # ---------------- CASE 1 : CONTEXT FOUND ---------------- #

        if context:

            prompt = f"""
    You are a document question-answering assistant.

Your job is to answer the user's question ONLY using the provided context.

Rules:

1. Use ONLY the information present in the context.
2. Do NOT use any external knowledge, assumptions, or prior information.
3. Do NOT make up facts.
4. If the answer is not present in the context, reply exactly:

I could not find this information in the uploaded documents.

5. If the context contains only part of the answer, provide only the information available in the context.
6. Structure the answer clearly using paragraphs, bullet points, or numbered lists when appropriate.
7. Explain the answer in your own words instead of copying the context verbatim whenever possible.

User Question:
{query}

Retrieved Context:
{context}


    Answer:
    """

            response = self.llm.invoke(prompt)

            print("\nLLM RESPONSE:")
            print(response.content)
            print("=" * 100)

            return response.content

        # ---------------- CASE 2 : NO CONTEXT FOUND ---------------- #

        fallback_prompt = f"""
    The user asked:

    {query}

    No relevant information was found in the uploaded documents.

    Please answer the question using your general knowledge.

    Before giving the answer, clearly mention that:

    1. The uploaded documents do not contain information related to this question.
    2. The following answer is based on your general knowledge.
    3. It may not be fully accurate because it is not derived from the uploaded documents.

    Then provide the best possible answer.
    """

        response = self.llm.invoke(fallback_prompt)

        print("\nGENERAL KNOWLEDGE RESPONSE:")
        print(response.content)
        print("=" * 100)

        return response.content

