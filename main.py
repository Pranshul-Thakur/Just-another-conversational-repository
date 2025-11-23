# Filename: main.py
from flask import Flask, render_template, request, jsonify
from gemini_bot import SentimentChatbot

app = Flask(__name__)

bot = SentimentChatbot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    
    # 1. Get Analysis
    sentiment_data = bot.get_sentiment(user_message)
    bot_reply = bot.generate_response(user_message, sentiment_data['label'])
    
    # 2. Log History
    bot.add_to_history(user_message, sentiment_data)
    
    return jsonify({
        'reply': bot_reply,
        'sentiment_label': sentiment_data['label'],
        'sentiment_score': sentiment_data['score']
    })

@app.route('/report', methods=['GET'])
def report():
    overall = bot.analyze_overall_sentiment()
    trend = bot.analyze_trend()
    
    return jsonify({
        'overall_sentiment': overall,
        'trend': trend
    })

if __name__ == '__main__':
    print("Starting Web Server at http://127.0.0.1:5000")
    app.run(debug=True)