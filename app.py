import streamlit as st
import os
import uuid
from datetime import datetime
from pathlib import Path

from src.chat_history import save_conversations, load_conversations
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

/* Active chat highlight */
.active-chat {
    background-color: #2a2d3e;
    border-radius: 8px;
    padding: 6px 10px;
    border-left: 3px solid #7c3aed;
    margin-bottom: 4px;
    font-size: 13px;
    color: #ccc;
    cursor: pointer;
}

/* Inactive chat */
.inactive-chat {
    background-color: #1a1a24;
    border-radius: 8px;
    padding: 6px 10px;
    margin-bottom: 4px;
    font-size: 13px;
    color: #888;
    cursor: pointer;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SESSION STATE INIT
# ✅ NEW: conversations dict stores all chats
#    each chat = { "title": str, "messages": list, "created_at": str }
# ---------------------------------------------------

def new_chat_id():
    return str(uuid.uuid4())[:8]

if "conversations" not in st.session_state:
    saved = load_conversations()

    if saved:
        # Restore from disk
        st.session_state.conversations = saved
        # Set current chat to the most recent one
        st.session_state.current_chat_id = list(saved.keys())[-1]
    else:
        # No history on disk — start fresh
        first_id = new_chat_id()
        st.session_state.conversations = {
            first_id: {
                "title": "New Chat",
                "messages": [],
                "created_at": datetime.now().strftime("%b %d, %H:%M")
            }
        }
        st.session_state.current_chat_id = first_id
        save_conversations(st.session_state.conversations)

# Safety: if current_chat_id got lost, reset to last chat
if st.session_state.current_chat_id not in st.session_state.conversations:
    st.session_state.current_chat_id = list(st.session_state.conversations.keys())[-1]

# Shortcut to current chat's messages
def current_messages():
    return st.session_state.conversations[st.session_state.current_chat_id]["messages"]

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    # ---------------------------------------------------
    # ✅ NEW CHAT BUTTON
    # ---------------------------------------------------

    if st.button("➕  New Chat", use_container_width=True):
        new_id = new_chat_id()
        st.session_state.conversations[new_id] = {
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.now().strftime("%b %d, %H:%M")
        }
        st.session_state.current_chat_id = new_id
        save_conversations(st.session_state.conversations)
        st.rerun()

    st.divider()

    # ---------------------------------------------------
    # ✅ CHAT HISTORY LIST
    # ---------------------------------------------------

    st.markdown("### 🕘 Chat History")

    # Show chats newest first
    sorted_chats = list(st.session_state.conversations.items())[::-1]

    for chat_id, chat_data in sorted_chats:

        is_active = (chat_id == st.session_state.current_chat_id)
        label = f"{'💬' if is_active else '🗨️'} {chat_data['title']}"
        caption = chat_data["created_at"]

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(label, key=f"switch_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
            st.caption(caption)

        with col2:
            # Delete individual chat
            if st.button("🗑", key=f"del_chat_{chat_id}"):
                del st.session_state.conversations[chat_id]
                save_conversations(st.session_state.conversations)
                # If we deleted the active chat, switch to another
                if st.session_state.current_chat_id == chat_id:
                    if st.session_state.conversations:
                        st.session_state.current_chat_id = list(st.session_state.conversations.keys())[-1]
                    else:
                        # No chats left — create a new one
                        new_id = new_chat_id()
                        st.session_state.conversations[new_id] = {
                            "title": "New Chat",
                            "messages": [],
                            "created_at": datetime.now().strftime("%b %d, %H:%M")
                        }
                        st.session_state.current_chat_id = new_id
                        save_conversations(st.session_state.conversations)
                st.rerun()

    st.divider()

    # ---------------------------------------------------
    # UPLOAD PDFs
    # ---------------------------------------------------

    st.header("📤 Upload PDFs")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:
            save_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.success("PDF uploaded successfully!")

        with st.spinner("Updating Vector Database..."):
            docs = load_all_documents("data")
            store = FaissVectorStore(FAISS_DIR)
            store.build_from_documents(docs)

        st.success("Vector Database Updated!")

    st.divider()

    # ---------------------------------------------------
    # PDF MANAGER
    # ---------------------------------------------------

    st.header("📁 PDF Manager")

    pdf_files = list(Path(DATA_DIR).glob("*.pdf"))

    if len(pdf_files) == 0:
        st.info("No PDFs uploaded.")
    else:
        with st.expander(f"📂 Uploaded PDFs ({len(pdf_files)})", expanded=False):
            for pdf in pdf_files:
                st.markdown(
                    f'<div class="pdf-card">📄 {pdf.name}</div>',
                    unsafe_allow_html=True
                )
                col1, col2 = st.columns([1, 1])

                with col1:
                    with open(pdf, "rb") as file:
                        st.download_button(
                            label="Preview",
                            data=file,
                            file_name=pdf.name,
                            mime="application/pdf",
                            key=f"preview_{pdf.name}"
                        )

                with col2:
                    if st.button("Delete", key=f"delete_{pdf.name}"):
                        try:
                            os.remove(pdf)
                            st.success(f"{pdf.name} deleted!")
                            docs = load_all_documents("data")
                            store = FaissVectorStore(FAISS_DIR)
                            store.build_from_documents(docs)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting file: {e}")

# ---------------------------------------------------
# MAIN AREA — show current chat title
# ---------------------------------------------------

current_chat = st.session_state.conversations[st.session_state.current_chat_id]

st.title(f"📚 {current_chat['title']}")
st.divider()
st.subheader("💬 Chat With Your PDFs")

# ---------------------------------------------------
# DISPLAY MESSAGES of current chat only
# ---------------------------------------------------

for message in current_messages():
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------

prompt = st.chat_input("Ask anything about your PDFs...")

if prompt:

    # ✅ Auto-title the chat from first message (first 40 chars)
    if current_chat["title"] == "New Chat" and len(current_messages()) == 0:
        current_chat["title"] = prompt[:40] + ("..." if len(prompt) > 40 else "")

    # Add user message
    current_messages().append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                rag = RAGSearch()
                response = rag.search_and_summarize(prompt, top_k=3)
            except Exception as e:
                response = f"Error: {e}"

        st.markdown(response)

    current_messages().append({"role": "assistant", "content": response})
    save_conversations(st.session_state.conversations)
    st.rerun()
