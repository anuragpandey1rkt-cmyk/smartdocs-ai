import streamlit as st
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Page Config
st.set_page_config(page_title="SmartDocs (Local)", page_icon="📘")
st.header("📘 SmartDocs: Enterprise Knowledge Assistant")

# 3. Sidebar for PDF Upload (Acts like Azure Blob Storage)
with st.sidebar:
    st.title("Document Ingestion")
    pdf_docs = st.file_uploader("Upload your PDFs", accept_multiple_files=True)
    
    if st.button("Process Documents"):
        if not pdf_docs:
            st.error("Please upload a PDF first.")
        else:
            with st.spinner("Indexing documents..."):
                # --- A. Read PDF (Ingestion) ---
                raw_text = ""
                for pdf in pdf_docs:
                    pdf_reader = PdfReader(pdf)
                    for page in pdf_reader.pages:
                        raw_text += page.extract_text()
                
                # --- B. Chunking (Preparation) ---
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                text_chunks = text_splitter.split_text(raw_text)
                
                # --- C. Vector Embedding (The "Azure AI Search" replacement) ---
                # We use FAISS (Local) instead of Azure Search for now
                embeddings = OpenAIEmbeddings()
                vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
                
                # Save index locally
                vector_store.save_local("faiss_index")
                st.success("Done! Documents are indexed and ready.")

# 4. Chat Interface
user_question = st.text_input("Ask a question about your documents:")

if user_question:
    # --- D. Retrieval (Finding relevant chunks) ---
    embeddings = OpenAIEmbeddings()
    try:
        # Load the local Vector DB
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)

        # --- E. Generation (The "Azure OpenAI" replacement) ---
        # We use standard GPT-3.5-turbo
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        
        # Custom Prompt to ensure it only answers from the PDF
        prompt_template = """
        Answer the question as detailed as possible from the provided context. 
        If the answer is not in the provided context, just say "I cannot find the answer in the documents."
        
        Context:
        {context}
        
        Question: 
        {question}
        
        Answer:
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        
        chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
        response = chain.invoke({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        
        st.write("### Answer:")
        st.write(response["output_text"])
        
    except Exception as e:
        st.error(f"Error: {e}. (Did you process the documents first?)")
