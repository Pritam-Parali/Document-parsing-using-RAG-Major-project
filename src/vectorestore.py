import os
import faiss
import numpy as np
import pickle
from typing import List,Any
from sentence_transformers import SentenceTransformer
from src.embedding import EmbeddingPipeline


class FaissVectorStore:
    def __init__(self,persist_dir :str ="faiss_store",embedding_model:str = "all-MiniLM-L6-v2",chunk_size=1000,chunk_overlap=200):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir,exist_ok=True)
        self.index = None
        self.metadata = []
        self.embedding_model = embedding_model
        self.model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"Loaded embedding model : {embedding_model}")
    
    def build_from_documents(self, documents: List[Any]):

        print(f"\nBuilding VectorStore from {len(documents)} raw documents ....")

        if not documents:
            print("No documents found.")
            self.index = None
            self.metadata = []
            return

        emb_pipe = EmbeddingPipeline(
            model_name=self.embedding_model,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        chunks = emb_pipe.chunk_documents(documents)

        if len(chunks) == 0:
            print("No chunks generated.")
            self.index = None
            self.metadata = []
            return

        print("Number of chunks:", len(chunks))

        embeddings = emb_pipe.embed_chunks(chunks)

        if embeddings is None or len(embeddings) == 0:
            print("No embeddings generated.")
            return

        print("Embeddings type:", type(embeddings))
        print("Embeddings shape:", np.array(embeddings).shape)

        metadatas = [
            {
                "text": chunk.page_content,
                "source": chunk.metadata.get("source", "Unknown")
            }
            for chunk in chunks
        ]

        self.add_embeddings(
            np.array(embeddings).astype("float32"),
            metadatas
        )


    def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Any] = None):
        if embeddings is None or embeddings.size == 0:
            print("No embeddings to add.")
            return
        print("Received embeddings shape:", embeddings.shape)
        if len(embeddings.shape) != 2:
            raise ValueError(
                f"Expected 2D embeddings but got shape {embeddings.shape}"
            )
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        if metadatas:
            self.metadata.extend(metadatas)
        print(f"Added {embeddings.shape[0]} vectors to Faiss index")

    def save(self):

        if self.index is None:
            print("No FAISS index found. Nothing to save.")
            return

        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")

        print(f"Saving FAISS index to: {os.path.abspath(faiss_path)}")
        print(f"Saving metadata to: {os.path.abspath(meta_path)}")

        faiss.write_index(self.index, faiss_path)

        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

        print(f"Saved {len(self.metadata)} metadata entries")
        print(f"Saved Faiss index and metadata to {self.persist_dir}")
    
    def load(self):
        faiss_path = os.path.join(self.persist_dir,"faiss.index")
        meta_path = os.path.join(self.persist_dir,"metadata.pkl")
        self.index = faiss.read_index(faiss_path)
        with open(meta_path,"rb") as f :
            self.metadata = pickle.load(f)
        print(f"Loaded Faiss index and metadata from {self.persist_dir}")

    def search(self,query_embedding : np.ndarray , top_k : int = 5):
        D,I = self.index.search(query_embedding,top_k)
        results = []
        for idx,dist in zip(I[0],D[0]):
            meta = self.metadata[idx] if idx < len(self.metadata) else None
            results.append({"index":idx,"distance":dist,"metadata":meta})
        return results
    
    def query(self, query_text: str, top_k: int = 5):
        print(f"\nQuerying vector store for: {query_text}")
        query_emb = self.model.encode(
            [query_text],
            convert_to_numpy=True
        ).astype("float32")
        faiss.normalize_L2(query_emb)
        return self.search(query_emb, top_k=top_k)
        