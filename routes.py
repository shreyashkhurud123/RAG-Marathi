from flask import request, jsonify
from app import app, db, limiter
from models import Document, Query
from rag_utils import extract_text_from_pdf, add_to_index, search_similar_chunks, get_answer
import logging

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Extract text from PDF
        text = extract_text_from_pdf(file)
        
        # Add to FAISS index
        vector_id = add_to_index(text, 0)  # 0 is temporary doc_id
        
        # Save to database
        doc = Document(
            filename=file.filename,
            content=text,
            vector_id=str(vector_id)
        )
        db.session.add(doc)
        db.session.commit()
        
        return jsonify({'message': 'Document uploaded successfully'}), 200
        
    except Exception as e:
        logging.error(f"Error in upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
@limiter.limit("20 per minute")
def query_documents():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        
        # Search similar documents
        similar_ids = search_similar_chunks(question)
        
        # Get relevant documents
        relevant_docs = Document.query.filter(
            Document.vector_id.in_([str(id) for id in similar_ids])
        ).all()
        
        # Combine context from relevant documents
        context = " ".join([doc.content for doc in relevant_docs])
        
        # Get answer from OpenAI
        answer = get_answer(question, context)
        
        # Save query and answer
        query = Query(question=question, answer=answer)
        db.session.add(query)
        db.session.commit()
        
        return jsonify({'answer': answer}), 200
        
    except Exception as e:
        logging.error(f"Error in query: {str(e)}")
        return jsonify({'error': str(e)}), 500
