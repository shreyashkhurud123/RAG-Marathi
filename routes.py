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
            return jsonify({'error': 'प्रश्न प्राप्त झाला नाही'}), 400

        question = data['question']

        # Search similar documents
        try:
            relevant_docs = search_similar_chunks(question)
        except Exception as e:
            logging.error(f"Error in search: {str(e)}")
            return jsonify({'error': str(e)}), 503

        if not relevant_docs:
            return jsonify({'error': 'या प्रश्नासंबंधित कोणतेही दस्तऐवज सापडले नाहीत'}), 404

        # Combine context from relevant documents
        context = " ".join([doc.content for doc in relevant_docs])

        # Get answer from OpenAI
        try:
            answer = get_answer(question, context)
        except Exception as e:
            logging.error(f"Error getting answer: {str(e)}")
            return jsonify({'error': str(e)}), 503

        # Save query and answer
        try:
            query = Query(question=question, answer=answer)
            db.session.add(query)
            db.session.commit()
        except Exception as e:
            logging.error(f"Error saving query: {str(e)}")
            # Don't return error here, as we still have the answer

        return jsonify({'answer': answer}), 200

    except Exception as e:
        logging.error(f"Error in query: {str(e)}")
        return jsonify({'error': 'तांत्रिक अडचणीमुळे प्रश्नाचे उत्तर देता येत नाही'}), 500