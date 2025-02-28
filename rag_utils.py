import os
import PyPDF2
import faiss
import numpy as np
from openai import OpenAI
from typing import List, Dict

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FAISS index
dimension = 1536  # OpenAI embedding dimension
index = faiss.IndexFlatL2(dimension)

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text"""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error getting embedding: {str(e)}")

def add_to_index(text: str, doc_id: int) -> int:
    """Add document embedding to FAISS index"""
    embedding = get_embedding(text)
    index.add(np.array([embedding]))
    return index.ntotal - 1

def search_similar_chunks(query: str, k: int = 3) -> List[int]:
    """Search for similar documents using FAISS"""
    query_embedding = get_embedding(query)
    D, I = index.search(np.array([query_embedding]), k)
    return I[0].tolist()

def get_answer(question: str, context: str) -> str:
    """Get answer from OpenAI using RAG context"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """You are a helpful assistant that answers 
                questions about Marathi government documents. Always respond in Marathi 
                language. Use the provided context to give accurate answers."""},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error getting answer from OpenAI: {str(e)}")
