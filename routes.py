from flask import request, jsonify
from app import app, db, limiter
from models import Document, Query
from rag_utils import search_similar_chunks, get_answer
import logging

@app.route('/query', methods=['POST'])
@limiter.limit("20 per minute")
def query_documents():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']

        # Search similar documents
        relevant_docs = search_similar_chunks(question)

        if not relevant_docs:
            return jsonify({'error': 'No relevant documents found'}), 404

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