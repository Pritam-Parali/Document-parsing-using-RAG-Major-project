from pathlib import Path
from typing import List,Any
import pandas as pd 
from langchain_community.document_loaders import PyMuPDFLoader,TextLoader,CSVLoader,Docx2txtLoader,UnstructuredExcelLoader,JSONLoader


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
        

       # CSV files
    from langchain_core.documents import Document

    csv_files = list(data_path.glob("**/*.csv"))
    print(f"\nFound {len(csv_files)} CSV files.")

    for csv_file in csv_files:
        print(f"Loading CSV : {csv_file}")

        try:
            # Read CSV using pandas
            df = pd.read_csv(csv_file)

            rows, cols = df.shape
            headers = list(df.columns)

            print(f"Rows:{rows} | Columns:{cols}")
            print(f"Headers:{headers}")

            # Create a summary document for metadata queries
            csv_summary = f"""
        CSV File Name: {csv_file.name}

        Number of Rows: {rows}
        Number of Columns: {cols}

        Column Names:
        {', '.join(headers)}
        """

            summary_doc = Document(
                page_content=csv_summary,
                metadata={
                    "source": str(csv_file),
                    "file_name": csv_file.name,
                    "file_type": "csv_summary",
                    "rows": rows,
                    "columns": cols,
                    "headers": ", ".join(headers)
                }
            )

            # Add summary document to vector store
            documents.append(summary_doc)

            # Load CSV rows normally
            loader = CSVLoader(str(csv_file))
            loaded = loader.load()

            print(f"Loaded {len(loaded)} CSV rows from {csv_file}")

            documents.extend(loaded)

        except Exception as e:
            print(f"Failed to load CSV {csv_file} : {e}")

    #  DOCX files
    docx_files = list(data_path.glob("**/*.docx"))
    print(f"\nFound {len(docx_files)} DOCX files.")
    for docx_file in docx_files:
        print(f"Loading DOCX : {docx_file}")
        try:
            loader = Docx2txtLoader(str(docx_file))
            loaded = loader.load()
            print(f"Loaded {len(loaded)} docx docs from {docx_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"Failed to load DOCX {docx_file} : {e}")
            

    #  Excel files (Handling both .xlsx and .xls)
    excel_files = list(data_path.glob("**/*.xlsx")) + list(data_path.glob("**/*.xls"))
    print(f"\nFound {len(excel_files)} Excel files.")
    for excel_file in excel_files:
        print(f"Loading Excel : {excel_file}")
        try:
            loader = UnstructuredExcelLoader(str(excel_file))
            loaded = loader.load()
            print(f"Loaded {len(loaded)} excel docs from {excel_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"Failed to load Excel {excel_file} : {e}")


    #  Text files 
    txt_files = list(data_path.glob("**/*.txt"))
    print(f"\nFound {len(txt_files)} TXT files.")
    for txt_file in txt_files:
        print(f"Loading TXT : {txt_file}")
        try:
            loader = TextLoader(str(txt_file))
            loaded = loader.load()
            print(f"Loaded {len(loaded)} txt docs from {txt_file}")
            documents.extend(loaded)
        except Exception as e:
            print(f"Failed to load TXT {txt_file} : {e}")
            
    print(f"\nTotal documents successfully loaded: {len(documents)}")
    return documents