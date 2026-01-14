import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

def create_vector_db():
    print("🔄 Loading PDFs from 'data' folder...")
    # A. Load PDF
    loader = PyPDFDirectoryLoader("data") # Put your PDF in a folder named 'data'
    documents = loader.load()
    
    # B. Split Text (Chunking)
    print("✂️ Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    text_chunks = text_splitter.split_documents(documents)
    
    # C. Create Embeddings (Using Free HuggingFace Model)
    # We use HuggingFace for embeddings so you don't need an OpenAI key for this part either!
    print("🧠 Creating Vector Embeddings (this may take a minute)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # D. Create & Save Database
    vector_store = FAISS.from_documents(text_chunks, embeddings)
    vector_store.save_local("faiss_index") # This creates the folder you upload to GitHub
    print("✅ Success! Database saved to 'faiss_index' folder.")

if __name__ == "__main__":
    create_vector_db()
