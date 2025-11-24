# Filename: main.py
from flask import Flask, render_template, request, jsonify
from gemini_bot import SentimentChatbot
import database

app = Flask(__name__)

database.init_db()
bot = SentimentChatbot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sessions', methods=['GET'])
def get_sessions():
    return jsonify(database.get_all_sessions())

@app.route('/new_chat', methods=['POST'])
def new_chat():
    message = request.json.get('message', 'New Chat')
    session_id = database.create_session(message)
    return jsonify({'session_id': session_id})

@app.route('/load_chat/<session_id>', methods=['GET'])
def load_chat(session_id):
    history = database.load_session(session_id)
    
    bot.conversation_history = [] 
    for msg in history:
        if msg['role'] == 'user':
            bot.add_to_history(msg['text'], msg['sentiment'])
            
    return jsonify({'history': history})

@app.route('/rename_chat', methods=['POST'])
def rename_chat():
    data = request.json
    if data.get('session_id') and data.get('new_title'):
        database.rename_session(data['session_id'], data['new_title'])
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id')

    if not session_id:
        session_id = database.create_session(user_message)

    sentiment_data = bot.get_sentiment(user_message)
    
    bot_reply = bot.generate_response(user_message, sentiment_data['label'])
    
    database.save_message(session_id, user_message, sentiment_data, bot_reply)
    bot.add_to_history(user_message, sentiment_data)
    
    return jsonify({
        'reply': bot_reply,
        'sentiment_label': sentiment_data['label'],
        'sentiment_score': sentiment_data['score'],
        'emotion': sentiment_data['emotion'],
        'session_id': session_id
    })

@app.route('/report', methods=['GET'])
def report():
    report_data = bot.generate_executive_summary()
    
    return jsonify({
        'overall_sentiment': report_data['sentiment'],
        'trend': report_data['trend'],
        'summary': report_data['summary']
    })

if __name__ == '__main__':
    print("Starting Web Server at http://127.0.0.1:5000")
    app.run(debug=True)