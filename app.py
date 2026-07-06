import streamlit as st
import os
import uuid
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.diagram_generator import generate_mermaid
from streamlit_mermaid import st_mermaid

from gtts import gTTS
from io import BytesIO

from PIL import Image
import pytesseract

from src.chat_history import save_conversations, load_conversations
from src.data_loader import load_all_documents
from src.vectorestore import FaissVectorStore
from src.search import RAGSearch

# OCR SETTINGS

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)


# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="RAG Documents Assistant",
    page_icon="📚",
    layout="wide"
)

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------

DATA_DIR = "data"
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

def new_chat_id():
    return str(uuid.uuid4())[:8]

if "conversations" not in st.session_state:
    saved = load_conversations()
    for chat in saved.values():
        if "flowcharts" not in chat:
            chat["flowcharts"] = []

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
                "flowcharts": [],
                "ocr_text": None,
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
    #  NEW CHAT BUTTON
    # ---------------------------------------------------

    if st.button("➕  New Chat", use_container_width=True):
        new_id = new_chat_id()
        st.session_state.conversations[new_id] = {
            "title": "New Chat",
            "messages": [],
            "flowcharts": [],
            "ocr_text": None,
            "created_at": datetime.now().strftime("%b %d, %H:%M")
        }
        st.session_state.current_chat_id = new_id
        save_conversations(st.session_state.conversations)
        st.rerun()

    st.divider()

    # ---------------------------------------------------
    #  CHAT HISTORY LIST
    # ---------------------------------------------------

    with st.expander(" Chat History",expanded=False):

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
    # SCREENSHOT OCR
    # ---------------------------------------------------

    st.header(" Flowchart and Text extract ")

    uploaded_image = st.file_uploader(
        "Upload Screenshot",
        type=["png", "jpg", "jpeg"],
        key="ocr_test"
    )

    if uploaded_image:

        image_path = os.path.join(
            DATA_DIR,
            uploaded_image.name
        )

        with open(image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())

        extracted_text = extract_text_from_image(
            image_path
        )

        current_chat = st.session_state.conversations[
            st.session_state.current_chat_id
        ]

        current_chat["ocr_text"] = extracted_text

        st.success("Screenshot processed!")

        with st.expander("View Extracted Text"):

            st.text_area(
                "OCR Text",
                extracted_text,
                height=250
            )

        st.divider()

    # ---------------------------------------------------
    # UPLOAD Documents
    # ---------------------------------------------------

    st.header(" Upload Documents")

    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf","csv", "docx", "xlsx", "xls", "txt"],
        accept_multiple_files=True
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:
            save_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.success("Document uploaded successfully!")

        with st.spinner("Updating Vector Database..."):
            docs = load_all_documents(DATA_DIR)
            store = FaissVectorStore(FAISS_DIR)
            store.index = None
            store.metadata = []
            store.build_from_documents(docs)
            store.save()

        st.success("Vector Database Updated!")
    st.divider()

    st.divider()

    # ---------------------------------------------------
    # Youtube video summarizer
    # ---------------------------------------------------

    st.header("YouTube Notes")

    youtube_url = st.text_input(
        "Paste YouTube URL"
    )

    if st.button("Generate Notes"):

        from src.youtube_loader import YouTubeLoader
        from src.youtube_chunker import split_transcript
        from src.youtube_notes import (
            summarize_chunk,
            generate_final_notes
        )
        from src.youtube_export import (
            save_notes_docx
        )

        with st.spinner("Fetching transcript..."):

            transcript = (
                YouTubeLoader.get_transcript(
                    youtube_url
                )
            )

        chunks = split_transcript(
            transcript
        )

        summaries = []

        progress = st.progress(0)

        for i, chunk in enumerate(chunks):

            summaries.append(
                summarize_chunk(chunk)
            )

            progress.progress(
                (i + 1) / len(chunks)
            )

        notes = generate_final_notes(
            summaries
        )

        save_notes_docx(
            notes,
            "youtube_notes.docx"
        )

        st.success("Notes Generated")

        st.download_button(
            "Download Notes",
            open(
                "youtube_notes.docx",
                "rb"
            ),
            file_name="youtube_notes.docx"
        )

        st.text_area(
            "Generated Notes",
            notes,
            height=400
        )


    # ---------------------------------------------------
    # Documents MANAGER
    # ---------------------------------------------------

    st.header(" Document Manager")

    pdf_files = list(Path(DATA_DIR).glob("*.*"))

    if len(pdf_files) == 0:
        st.info("No Documents uploaded.")
    else:
        with st.expander(f"📂 Uploaded Document ({len(pdf_files)})", expanded=False):
            for pdf in pdf_files:
                st.markdown(
                    f'<div class="pdf-card">📄 {pdf.name}</div>',
                    unsafe_allow_html=True
                )
                if pdf.suffix.lower()=="csv":
                    try:
                        df=pd.read_csv(pdf)
                        st.caption(f" 📊 {df.shape[0]}Rows x {df.shape[1]}columns")
                        
                    except Exception as e:
                        st.caption(f"Could not read csv{e}")

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
                            # Delete physical file
                            os.remove(pdf)
                            # Load remaining documents
                            docs = load_all_documents(DATA_DIR)
                            # If no documents remain, remove FAISS completely
                            if len(docs) == 0:

                                faiss_file = os.path.join(
                                    FAISS_DIR,
                                    "faiss.index"
                                )

                                metadata_file = os.path.join(
                                    FAISS_DIR,
                                    "metadata.pkl"
                                )

                                if os.path.exists(faiss_file):
                                    os.remove(faiss_file)

                                if os.path.exists(metadata_file):
                                    os.remove(metadata_file)

                                st.success(
                                    f"{pdf.name} deleted! Vector database cleared."
                                )

                            else:

                                # Rebuild FAISS using remaining documents
                                store = FaissVectorStore(FAISS_DIR)

                                store.index = None
                                store.metadata = []

                                store.build_from_documents(docs)
                                store.save()

                                st.success(
                                    f"{pdf.name} deleted! Vector database rebuilt."
                                )

                            st.rerun()

                        except Exception as e:
                            st.error(f"Error deleting file: {e}")

# ---------------------------------------------------
# MAIN AREA — show current chat title
# ---------------------------------------------------

current_chat = st.session_state.conversations[st.session_state.current_chat_id]

st.title(f" {current_chat['title']}")
st.divider()
st.subheader(" Chat With Your Documents")

# ---------------------------------------------------
# DISPLAY MESSAGES of current chat only
# ---------------------------------------------------

for i, message in enumerate(current_messages()):

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Read assistant messages aloud
        if message["role"] == "assistant":

            if st.button("🔊 Read Aloud", key=f"tts_{i}"):

                try:

                    tts = gTTS(
                        text=message["content"],
                        lang="en"
                    )

                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)

                    st.audio(
                        audio_bytes.getvalue(),
                        format="audio/mp3"
                    )

                except Exception as e:
                    st.error(f"TTS Error: {e}")

    # Show diagram BELOW the bot message
    if "diagram" in message:

        st.code(message["diagram"])

        try:

            st_mermaid(
                message["diagram"],
                key=f"diagram_{i}"
            )

        except Exception as e:

            st.error(f"Diagram Error: {e}")

        st.divider()

# ---------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------


prompt = st.chat_input("Ask anything about your Documents...")

if prompt:

    #  Auto-title the chat from first message (first 40 chars)
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

                if "flowchart" in prompt.lower() or "diagram" in prompt.lower():

                    rag = RAGSearch()

                    prompt_lower = prompt.lower()

                    topic = prompt

                    for phrase in [
                        "create a flowchart of",
                        "create flowchart of",
                        "create a diagram of",
                        "create diagram of",
                    ]:
                        if phrase in prompt_lower:
                            index = prompt_lower.find(phrase)
                            topic = prompt[index + len(phrase):].strip()
                            break

                    context = rag.search_and_summarize(topic, top_k=3)

                    mermaid_code = generate_mermaid(context)
                    mermaid_code = mermaid_code.replace("|>", "|")

                    current_chat.setdefault("flowcharts", []).append(mermaid_code)

                    response = {
                        "text": "✅ Flowchart generated.",
                        "diagram": mermaid_code
                    }

                elif current_chat.get("ocr_text"):

                    from langchain_groq import ChatGroq
                    from dotenv import load_dotenv
                    import os

                    load_dotenv()

                    llm = ChatGroq(
                        groq_api_key=os.getenv("groq_api_key"),
                        model_name="llama-3.3-70b-versatile"
                    )

                    ocr_text = current_chat["ocr_text"]

                    ocr_prompt = f"""
                You are helping the user understand a screenshot.

                Screenshot Text:
                {ocr_text}

                User Question:
                {prompt}

                Answer the user's question using the screenshot text.
                If the answer is not present, clearly say so.
                """

                    response = llm.invoke(ocr_prompt).content

                else:

                    rag = RAGSearch()
                    response = rag.search_and_summarize(
                                prompt,
                                chat_history=current_messages(),
                                top_k=5
                            )

                    response = rag.search_and_summarize(prompt, top_k=3)

            except Exception as e:
                response = f"Error: {e}"
            

    if isinstance(response, dict):
        current_messages().append({
            "role": "assistant",
            "content": response["text"],
            "diagram": response["diagram"]
        })
    else:
        current_messages().append({
            "role": "assistant",
            "content": response
        })
    save_conversations(st.session_state.conversations)
    st.rerun()

# ---------------------------------------------------
# SCREENSHOT FLOWCHART BUTTON
# ---------------------------------------------------

if current_chat.get("ocr_text"):

    st.divider()

    if st.button("📊 Generate Screenshot Flowchart"):

        try:

            mermaid_code = generate_mermaid(
                current_chat["ocr_text"]
            )

            mermaid_code = mermaid_code.replace("|>", "|")

            current_messages().append({
                "role": "assistant",
                "content": "✅ Screenshot Flowchart Generated.",
                "diagram": mermaid_code
            })

            save_conversations(
                st.session_state.conversations
            )

            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")