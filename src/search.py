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


    def search_and_summarize(self, query: str,chat_history=None, top_k: int = 5) -> str:

        csv_files = list(Path("data").glob("*.csv"))

        for csv_file in csv_files:
            csv_answer = analyze_csv(
                query,
                str(csv_file)
            )
            if csv_answer:
                return csv_answer

        results = self.vectorstore.query(query, top_k=top_k)

        RELEVANCE_THRESHOLD = 0.35

        filtered_results = []

        for r in results:

            score = r.get("distance", 0)

            if score > RELEVANCE_THRESHOLD:
                filtered_results.append(r)

        texts = [
            r["metadata"].get("text", "")
            for r in filtered_results
            if r["metadata"]
        ]

        context = "\n\n".join(texts).strip()

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

        print("\nCONTEXT SENT TO LLM:")
        print("=" * 100)
        print(context[:3000])
        print("=" * 100)
        

        # ---------------- CASE 1 : CONTEXT FOUND ---------------- #
        # ---------------- Reading chat history ---------------- #
        history_text = ""
        if chat_history:
            history_text = "\n".join(
                [
                    f"{msg['role']}: {msg['content']}"
                    for msg in chat_history[-6:]
                ]
            )

        if context:
            prompt = f"""
                You are a helpful AI assistant.
                Use the retrieved context as the FIRST source of information.
                Rules:
                1. If the context contains the answer, answer using the context.
                2. If the context partially contains the answer, combine the context with your own knowledge.
                3. If the context does NOT contain the answer, ignore the context and answer using your own knowledge.
                4. Never say "I cannot answer" or "I could not find the information".
                5. Always provide the best possible answer.
                6.If possible use bullet points to answer
                Conversation History:
                {history_text}
                Current User Question:
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

        if len(filtered_results) == 0:
                fallback_prompt = f"""
                    You are a helpful AI assistant.

                    Conversation History:
                    {history_text}

                    Current User Question:
                    {query}

                    No relevant information was found in the uploaded documents.

                    Answer using your general knowledge while considering the conversation history.
                    """

        response = self.llm.invoke(fallback_prompt)
        return response.content

