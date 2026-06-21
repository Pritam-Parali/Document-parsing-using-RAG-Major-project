from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_transcript(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300
    )

    chunks = splitter.split_text(text)

    return chunks