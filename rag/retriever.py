import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from rag.loader import load_and_split
from dotenv import load_dotenv

load_dotenv()


def create_vector_store(persist_directory: str = ".chroma"):
    """Create ChromaDB vector store from documents."""
    print("Creating vector store...")
    chunks = load_and_split()

    embeddings = OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    print(f"Vector store created with {vector_store._collection.count()} chunks")
    return vector_store


def load_vector_store(persist_directory: str = ".chroma"):
    """Load existing vector store from disk."""
    embeddings = OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    return vector_store


def get_retriever(persist_directory: str = ".chroma"):
    """Get retriever - creates vector store if it doesn't exist."""
    if not os.path.exists(persist_directory):
        vector_store = create_vector_store(persist_directory)
    else:
        print("Loading existing vector store...")
        vector_store = load_vector_store(persist_directory)

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    return retriever