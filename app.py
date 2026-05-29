import streamlit as st
import os
from pathlib import Path

from src.data_loader import load_all_documents
from src.vectorestore import FaissVectorStore
from src.search import RAGSearch

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="RAG PDF Assistant",
    page_icon="📚",
    layout="wide"
)

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------

DATA_DIR = "data/pdf"
FAISS_DIR = "faiss_store"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

section[data-testid="stSidebar"] {
    background-color: #161A23;
}

.pdf-card {
    background-color: #1E1E1E;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #333;
}

.stChatMessage {
    background-color: #1E1E1E;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 10px;
}

.stChatInputContainer {
    border-top: 1px solid #333;
    padding-top: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("📚 RAG PDF Assistant")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.header("📤 Upload PDFs")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    # ---------------------------------------------------
    # SAVE PDFs
    # ---------------------------------------------------

    if uploaded_files:

        for uploaded_file in uploaded_files:

            save_path = os.path.join(DATA_DIR, uploaded_file.name)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.success("PDF uploaded successfully!")

        # rebuild vector db
        with st.spinner("Updating Vector Database..."):

            docs = load_all_documents("data")

            store = FaissVectorStore(FAISS_DIR)

            store.build_from_documents(docs)

        st.success("Vector Database Updated!")

    st.divider()

    # ---------------------------------------------------
    # DROPDOWN PDF SECTION
    # ---------------------------------------------------

    st.header("📁 PDF Manager")

    pdf_files = list(Path(DATA_DIR).glob("*.pdf"))

    if len(pdf_files) == 0:

        st.info("No PDFs uploaded.")

    else:

        with st.expander(f"📂 Uploaded PDFs ({len(pdf_files)})", expanded=False):

            for pdf in pdf_files:

                st.markdown(
                    f"""
                    <div class="pdf-card">
                        📄 {pdf.name}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns([1, 1])

                # ---------------------------------------------------
                # PREVIEW BUTTON
                # ---------------------------------------------------

                with col1:

                    with open(pdf, "rb") as file:

                        st.download_button(
                            label="Preview",
                            data=file,
                            file_name=pdf.name,
                            mime="application/pdf",
                            key=f"preview_{pdf.name}"
                        )

                # ---------------------------------------------------
                # DELETE BUTTON
                # ---------------------------------------------------

                with col2:

                    if st.button("Delete", key=f"delete_{pdf.name}"):

                        try:

                            # delete pdf
                            os.remove(pdf)

                            st.success(f"{pdf.name} deleted!")

                            # rebuild vector db
                            docs = load_all_documents("data")

                            store = FaissVectorStore(FAISS_DIR)

                            store.build_from_documents(docs)

                            st.rerun()

                        except Exception as e:

                            st.error(f"Error deleting file: {e}")

# ---------------------------------------------------
# MAIN CHAT SECTION
# ---------------------------------------------------

st.divider()

st.subheader("💬 Chat With Your PDFs")

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------
# DISPLAY CHAT
# ---------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# ---------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------

prompt = st.chat_input("Ask anything about your PDFs...")

if prompt:

    # ---------------------------------------------------
    # USER MESSAGE
    # ---------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):

        st.markdown(prompt)

    # ---------------------------------------------------
    # ASSISTANT RESPONSE
    # ---------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                rag = RAGSearch()

                response = rag.search_and_summarize(
                    prompt,
                    top_k=3
                )

            except Exception as e:

                response = f"Error: {e}"

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )