from flask import Flask, render_template, request, jsonify, send_file
from gemini_bot import SentimentChatbot
import database
import io
import json

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

@app.route('/download_report/<file_format>', methods=['GET'])
def download_report(file_format):
    
    session_id = request.args.get('session_id')
    session_title = "Current_Session"
    
    if session_id:
        all_sessions = database.get_all_sessions()
        for sess in all_sessions:
            if sess['id'] == session_id:
                session_title = sess['title']
                break

    safe_filename = "".join([c for c in session_title if c.isalnum() or c in (' ', '-', '_', '.')]).strip()
    safe_filename = safe_filename.replace(" ", "_")
    
    if not safe_filename:
        safe_filename = "Session_Report"

    report_data = bot.generate_executive_summary()
    insight = report_data.get('summary', {})
    
    summary_text = insight.get('summary', 'N/A')
    emotion = insight.get('Summarised emotion of chat', 'N/A')
    score = insight.get('sentiment_score', 'N/A')

    chat_log = []
    for entry in bot.conversation_history:
        log_entry = {
            "user_message": entry['text'],
            "sentiment": entry['sentiment']['label'],
            "score": entry['sentiment']['score'],
            "emotion": entry['sentiment']['emotion']
        }
        chat_log.append(log_entry)

    if file_format == 'json':
        export_obj = {
            "session_name": session_title,
            "report_type": "Detailed Sentiment Audit",
            "analytics": {
                "overall_review": report_data['sentiment'],
                "conversation_flow": report_data['trend'],
                "dominant_emotion": emotion,
                "average_score": score,
                "executive_summary": summary_text
            },
            "transcript_analysis": chat_log
        }
        
        mem = io.BytesIO()
        mem.write(json.dumps(export_obj, indent=4).encode('utf-8'))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name=f'{safe_filename}_report.json', mimetype='application/json')

    elif file_format == 'txt':
        lines = [
            "SENTIMENT AUDIT REPORT",
            f"Session Name: {session_title}",
            "",
            "EXECUTIVE SUMMARY",
            f"Overall Review:    {report_data['sentiment']}",
            f"Conversation Flow: {report_data['trend']}",
            f"Dominant Emotion:  {emotion} (Avg Score: {score})",
            f"Summary:           {summary_text}",
            "",
            "TRANSCRIPT ANALYSIS"
        ]
        
        for i, log in enumerate(chat_log, 1):
            lines.append(f"{i}. User: {log['user_message']}")
            lines.append(f"   Analysis: {log['sentiment']} | {log['emotion']} ({log['score']:.2f})")
            lines.append("") 
            
        mem = io.BytesIO()
        mem.write("\n".join(lines).encode('utf-8'))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name=f'{safe_filename}_report.txt', mimetype='text/plain')

    return "Invalid format", 400

if __name__ == '__main__':
    print("Starting Web Server at http://127.0.0.1:5000")
    app.run(debug=True)