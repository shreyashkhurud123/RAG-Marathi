import os
import PyPDF2
import faiss
import numpy as np
from openai import OpenAI
from typing import List, Dict
import logging
from models import Document
from app import db
import time
from functools import lru_cache

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FAISS index
dimension = 1536  # OpenAI embedding dimension
index = faiss.IndexFlatL2(dimension)

def load_documents_from_directory(directory: str) -> None:
    """Load all PDF documents from a directory into the database and FAISS index"""
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            try:
                # Check if document already exists
                existing_doc = Document.query.filter_by(filepath=filepath).first()
                if existing_doc:
                    continue

                # Extract text from PDF
                text = extract_text_from_pdf(filepath)

                # Get embedding and add to FAISS index
                vector_id = add_to_index(text)

                # Save to database
                doc = Document(
                    filepath=filepath,
                    title=os.path.splitext(filename)[0],
                    content=text,
                    vector_id=str(vector_id)
                )
                db.session.add(doc)
                db.session.commit()
                logging.info(f"Added document: {filename}")

            except Exception as e:
                logging.error(f"Error processing {filename}: {str(e)}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text with retry logic and caching"""
    max_retries = 3
    base_delay = 1  # Start with 1 second delay

    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise Exception(f"Error getting embedding after {max_retries} attempts: {str(e)}")

            # Calculate delay with exponential backoff
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            logging.warning(f"Embedding API call failed, retrying in {delay}s. Error: {str(e)}")
            time.sleep(delay)

def add_to_index(text: str) -> int:
    """Add document embedding to FAISS index"""
    embedding = get_embedding(text)
    index.add(np.array([embedding]))
    return index.ntotal - 1

def search_similar_chunks(query: str, k: int = 3) -> List[Document]:
    """Search for similar documents using FAISS"""
    try:
        query_embedding = get_embedding(query)
        D, I = index.search(np.array([query_embedding]), k)

        # Get documents from database
        relevant_docs = Document.query.filter(
            Document.vector_id.in_([str(i) for i in I[0]])
        ).all()

        return relevant_docs
    except Exception as e:
        logging.error(f"Error in search_similar_chunks: {str(e)}")
        raise Exception("तांत्रिक अडचणीमुळे शोध करता आला नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.")

def get_answer(question: str, context: str) -> str:
    """Get answer from OpenAI using RAG context with retry logic"""
    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
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
            if attempt == max_retries - 1:  # Last attempt
                logging.error(f"Final attempt failed: {str(e)}")
                return "माफ करा, तांत्रिक अडचणीमुळे आम्ही तुमच्या प्रश्नाचे उत्तर देऊ शकत नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."

            delay = base_delay * (2 ** attempt)
            logging.warning(f"OpenAI API call failed, retrying in {delay}s. Error: {str(e)}")
            time.sleep(delay)