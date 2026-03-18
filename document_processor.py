import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


def process_uploaded_file(uploaded_file) -> tuple[int, str]:
    """
    Process an uploaded file and add it to the vector store.
    
    Returns:
        tuple of (chunks_added, status_message)
    """
    # Save uploaded file to temp location
    suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".txt"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        # Load document
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding="utf-8")

        documents = loader.load()

        # Add source metadata
        for doc in documents:
            doc.metadata["source"] = f"uploaded/{uploaded_file.name}"

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
        )
        chunks = splitter.split_documents(documents)

        if not chunks:
            return 0, "No content found in the file."

        # Add to existing vector store
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        vector_store = Chroma(
            persist_directory=".chroma",
            embedding_function=embeddings
        )
        vector_store.add_documents(chunks)

        return len(chunks), f"✅ Successfully added {len(chunks)} chunks from '{uploaded_file.name}'"

    except Exception as e:
        return 0, f"❌ Error processing file: {str(e)}"

    finally:
        os.unlink(tmp_path)
       