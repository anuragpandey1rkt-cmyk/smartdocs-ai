# 📘 SmartDoc AI - Enterprise Knowledge Assistant

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://smartdocs-ai.streamlit.app)

**🔗 Live Demo:** [Click here to view the App](https://smartdocs-ai.streamlit.app)


## 🚀 Overview
SmartDoc AI is an intelligent document processing system designed to solve the "Knowledge Silo" problem in large organizations. It transforms static employee handbooks and technical manuals into an interactive **Digital Assistant**.

Employees can query documents, raise support tickets, and get instant answers using **Retrieval-Augmented Generation (RAG)**, while Administrators get a real-time dashboard of organizational issues.

## ⚠️ Cloud Infrastructure Note
> **Note to Evaluators:** During the development phase, the assigned Azure Tenant experienced a persistent access error (`AADSTS16000`), preventing the direct provisioning of Azure OpenAI and Azure SQL resources. 
> 
> To ensure a functional submission, I implemented a **Cloud-Agnostic Architecture** using industry-standard equivalents (PostgreSQL, Llama-3). The application is architected to be "Lift-and-Shift" ready for Azure immediately upon access restoration.

## 🏗️ Architecture & Azure Migration Path
I designed this application to map 1:1 with Microsoft Azure services.

| Current Component | Azure Target Service (Intended Architecture) | Why they are compatible |
| :--- | :--- | :--- |
| **Frontend:** Streamlit Cloud | **Azure App Service (Web Apps)** | Both support Python containerized deployment. |
| **AI Engine:** Groq (Llama-3) | **Azure OpenAI (GPT-4o)** | Both utilize standard LLM API patterns. |
| **Database:** Neon PostgreSQL | **Azure Database for PostgreSQL** | Identical connection strings and SQL syntax. |
| **Vector Search:** FAISS (Local) | **Azure AI Search** | Both manage vector embeddings for RAG. |

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python)
* **AI Engine:** Groq (Llama-3 8B) for high-speed inference
* **Database:** Cloud PostgreSQL (Neon) for persistent storage
* **Processing:** PyPDF2 for text extraction
* **Accessibility:** gTTS for audio summaries

## ✨ Key Features
1.  **📄 Intelligent Summarization:** Compresses complex documents into key executive insights.
2.  **❓ Interactive Q&A:** Chat with your document using natural language (RAG).
3.  **🛠️ Employee Service Desk:** Integrated ticketing system for raising IT/HR requests directly from the app.
4.  **📊 Admin Dashboard:** Role-based analytics dashboard to monitor tickets and user activity.
5.  **🎧 Audio Mode:** Converts text summaries to speech for accessibility.
6.  **🔐 Secure Auth:** Enterprise-grade login system with Hashed Passwords (SHA-256) and Role-Based Access Control (Admin vs. Employee).

## 🔮 Future Scope
* **Azure Blob Storage Integration:** For centralized, secure file management.
* **Power Automate Integration:** To email HR automatically when a new ticket is raised.
* **Multi-Document Support:** Cross-referencing multiple manuals simultaneously.
