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
        texts = [r["metadata"].get("text", "") for r in results if r["metadata"]]
        context = "\n\n".join(texts)
        if not context:
            return "No relevant documents found."
        prompt = f"""Summarize the following context for the query: '{query}'\n\nContext:\n{context}\n\nSummary:"""
        response = self.llm.invoke([prompt])
        return response.content

