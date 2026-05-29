from pathlib import Path
from typing import List,Any
from langchain_community.document_loaders import PyMuPDFLoader,TextLoader,csv_loader,Docx2txtLoader,UnstructuredExcelLoader,JSONLoader


def load_all_documents(data_dir:str) -> List[Any]:
    """
    Loading all the files from the folder and converting to langchain document structure
    Supported files : Pdf,text,csv 
    """

    # Using project root data folder
    data_path = Path(data_dir).resolve()
    print(f"Data path : {data_path}\n")
    documents = []

    #pdf files
    pdf_files = list(data_path.glob("**/*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files : {[str(f) for f in pdf_files]}")
    for pdf_file in pdf_files:
        print(f"\nLoading PDF : {pdf_file}")
        try:
            loader = PyMuPDFLoader(str(pdf_file))
            loaded  = loader.load()
            print(f"\nLoaded {len(loaded)} pdf docs from {pdf_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"\nFailed to load PDF {pdf_file} : {e}")

    return documents