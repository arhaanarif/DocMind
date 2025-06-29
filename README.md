# DocMind
A smart AI-powered tool to **summarize, understand and query research papers** using modern LLMs and RAG(Retrieval-Augmented Generation)

## 🔍 Overview
This **research paper analyzer** is an end-to-end application designed to help users
- Upload and process research paper PDFs
- Automatically extract, clean and summarize the content
- Interact with the paper via chatbot powered by an open-source LLM from hugging face
- Utilize a RAG pipeline to provide accurate and context-aware responses
- Authenticate users using IBM Cloud App ID
- Store vector embeddings with ChromaDB and metadata in IBM Db2

## 🛠️ Stack Overview

| Layer            | Tech Used                                 |
|------------------|-------------------------------------------|
| Backend API      | FastAPI                                   |
| Authentication   | IBM Cloud App ID                          |
| LLM Integration  | Hugging Face (Mistral 7B via Colab)       |
| RAG & Vector DB  | ChromaDB                                  |
| PDF Processing   | pdfplumber, PyMuPDF                       |
| Database         | IBM Db2                                   |
| Frontend         | Minimal HTML + JS (simple UI)             |
| API Testing      | Postman                                   |


