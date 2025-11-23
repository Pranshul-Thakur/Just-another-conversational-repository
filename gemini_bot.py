#gemini_bot.py
import google.generativeai as genai
import statistics
import json
import logging
import time
from typing import List, Dict, Any, Optional
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatbotError(Exception):
    pass

class SentimentChatbot:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            logger.error("API Key missing.")
            raise ChatbotError("GEMINI_API_KEY not found. Please set it in .env file.")
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=Config.MODEL_NAME,
                system_instruction=Config.SYSTEM_INSTRUCTION
            )
            self.chat_session = self.model.start_chat(history=[])
            self.conversation_history: List[Dict[str, Any]] = []
            self.last_turn_data: Optional[Dict[str, Any]] = None
            logger.info("SentimentChatbot initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize Gemini model: {e}")
            raise ChatbotError(f"Initialization failed: {e}")

    def process_turn(self, text: str) -> Dict[str, Any]:
        attempt = 0
        while attempt < Config.MAX_RETRIES:
            try:
                response = self.chat_session.send_message(
                    text,
                    generation_config={"response_mime_type": "application/json"}
                )
                try:
                    data = json.loads(response.text)
                    self._validate_response_structure(data)
                    self.last_turn_data = data
                    return data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from API. Attempt {attempt + 1}")
                    raise ValueError("Malformed JSON response")
                    
            except Exception as e:
                attempt += 1
                logger.error(f"API Call failed (Attempt {attempt}/{Config.MAX_RETRIES}): {e}")
                time.sleep(Config.RETRY_DELAY)
        logger.error("Max retries reached. Returning fallback response.")
        return self._get_fallback_response()

    def _validate_response_structure(self, data: Dict[str, Any]) -> None:
        required_keys = ["sentiment_label", "sentiment_score", "reply"]
        if not all(key in data for key in required_keys):
            raise ValueError(f"Missing keys in API response. Expected {required_keys}")

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.0,
            "reply": "I'm currently experiencing connection issues. Please try again later."
        }

    def get_sentiment(self, text: str) -> Dict[str, Any]:
        data = self.process_turn(text)
        return {
            "label": data.get("sentiment_label", "Neutral"),
            "score": data.get("sentiment_score", 0.0),
            "breakdown": {} 
        }

    def generate_response(self, text: str, sentiment_label: str) -> str:
        if self.last_turn_data:
            return self.last_turn_data.get("reply", "Error retrieving reply.")
        return "I missed that. Could you say it again?"

    def add_to_history(self, user_text: str, sentiment_data: Dict[str, Any]) -> None:
        self.conversation_history.append({
            "text": user_text,
            "sentiment": sentiment_data
        })

    def analyze_overall_sentiment(self) -> str:
        if not self.conversation_history:
            return "No conversation recorded."
            
        scores = [entry['sentiment']['score'] for entry in self.conversation_history]
        avg_score = statistics.mean(scores)
        
        if avg_score >= Config.SENTIMENT_THRESHOLD_POSITIVE:
            return f"Positive (Avg Score: {avg_score:.2f})"
        elif avg_score <= Config.SENTIMENT_THRESHOLD_NEGATIVE:
            return f"Negative (Avg Score: {avg_score:.2f})"
        else:
            return f"Neutral (Avg Score: {avg_score:.2f})"

    def analyze_trend(self) -> str:
        if len(self.conversation_history) < 2:
            return "Not enough data for trend analysis."
            
        midpoint = len(self.conversation_history) // 2
        first_half = self.conversation_history[:midpoint]
        second_half = self.conversation_history[midpoint:]
        
        avg_first = statistics.mean([x['sentiment']['score'] for x in first_half])
        avg_second = statistics.mean([x['sentiment']['score'] for x in second_half])
        
        diff = avg_second - avg_first
        if diff > 0.2:
            return "Improving Mood lifted over time)"
        elif diff < -0.2:
            return "Declining (Mood worsened over time)"
        else:
            return "Stable (Consistent mood)"