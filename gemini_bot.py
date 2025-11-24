import google.generativeai as genai
import statistics
import json
import logging
import time
import re
from typing import List, Dict, Any, Optional
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatbotError(Exception):
    pass

class SentimentChatbot:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ChatbotError("GEMINI_API_KEY not found.")
        
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=Config.MODEL_NAME,
                system_instruction=Config.SYSTEM_INSTRUCTION
            )
            self.chat_session = self.model.start_chat(history=[])
            self.conversation_history: List[Dict[str, Any]] = []
            self.last_turn_data: Optional[Dict[str, Any]] = None
        except Exception as e:
            raise ChatbotError(f"Initialization failed: {e}")

    def _calculate_final_score(self, text: str, base_score: float) -> float:
        score = base_score
        letters = [c for c in text if c.isalpha()]
        if len(letters) >= 4:
            upper_count = sum(1 for c in letters if c.isupper())
            if (upper_count / len(letters)) > 0.6:
                score *= Config.INTENSITY_MULTIPLIER

        text_lower = text.lower()
        for bad_word in Config.PROFANITY_LIST:
            if re.search(r'\b' + re.escape(bad_word) + r'\b', text_lower):
                score -= Config.PROFANITY_PENALTY
        return max(-1.0, min(1.0, score))

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
                    raw_score = data['sentiment_score']
                    final_score = self._calculate_final_score(text, raw_score)
                    data['sentiment_score'] = final_score
                    if final_score <= -0.8 and data['emotion'] not in ["Anger", "Disgust", "Fear"]:
                        data['emotion'] = "Anger" 
                            
                    self.last_turn_data = data
                    
                    if final_score >= Config.SENTIMENT_THRESHOLD_POSITIVE:
                        data['sentiment_label'] = "Positive"
                    elif final_score <= Config.SENTIMENT_THRESHOLD_NEGATIVE:
                        data['sentiment_label'] = "Negative"
                    else:
                        data['sentiment_label'] = "Neutral"
                        
                    return data
                except json.JSONDecodeError:
                    raise ValueError("Malformed JSON response")
            except Exception as e:
                attempt += 1
                time.sleep(Config.RETRY_DELAY)
        
        return self._get_fallback_response()

    def _validate_response_structure(self, data: Dict[str, Any]) -> None:
        required_keys = ["sentiment_score", "reply", "emotion"]
        if not all(key in data for key in required_keys):
            if "emotion" not in data:
                data["emotion"] = "Neutral"
            else:
                raise ValueError(f"Missing keys. Got: {data.keys()}")

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.0,
            "emotion": "Neutral",
            "reply": "Connection error. Please try again."
        }

    def get_sentiment(self, text: str) -> Dict[str, Any]:
        data = self.process_turn(text)
        return {
            "label": data.get("sentiment_label", "Neutral"),
            "score": data.get("sentiment_score", 0.0),
            "emotion": data.get("emotion", "Neutral")
        }

    def generate_response(self, text: str, sentiment_label: str) -> str:
        if self.last_turn_data:
            return self.last_turn_data.get("reply", "Error.")
        return "I missed that."

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
            return "Positive"
        elif avg_score <= Config.SENTIMENT_THRESHOLD_NEGATIVE:
            return "Negative"
        else:
            return "Neutral"

    def analyze_trend(self) -> str:
        if len(self.conversation_history) < 2:
            return "Not enough data."
        mid = len(self.conversation_history) // 2
        avg_1 = statistics.mean([x['sentiment']['score'] for x in self.conversation_history[:mid]])
        avg_2 = statistics.mean([x['sentiment']['score'] for x in self.conversation_history[mid:]])
        diff = avg_2 - avg_1
        
        if diff > 0.2: return "Improving"
        elif diff < -0.2: return "Declining"
        else: return "Stable"

    def generate_executive_summary(self) -> Dict[str, Any]:
        if not self.conversation_history:
            return {"sentiment": "No Data", "trend": "None", "summary": {}}

        overall_sent = self.analyze_overall_sentiment()
        trend = self.analyze_trend()
        
        scores = [entry['sentiment']['score'] for entry in self.conversation_history]
        avg_score = round(statistics.mean(scores), 2)

        transcript = "\n".join([f"User: {msg['text']}" for msg in self.conversation_history])
        
        summary_prompt = f"""
        Read this chat transcript:
        {transcript}
        
        Provide a JSON object with exactly two keys:
        1. "summary": A 1-sentence opinion on how the conversation went.
        2. "emotion": The single dominant emotion of the entire chat.
        """
        
        try:
            summary_model = genai.GenerativeModel(Config.MODEL_NAME)
            response = summary_model.generate_content(
                summary_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            summary_text = data.get("summary", "No summary available.")
            chat_emotion = data.get("emotion", "Neutral")
            
        except Exception:
            summary_text = "Analysis failed."
            chat_emotion = "Unknown"

        final_json_insight = {
            "sentiment_score": avg_score,
            "Summarised emotion of chat": chat_emotion,
            "summary": summary_text
        }

        return {
            "sentiment": overall_sent,
            "trend": trend,
            "summary": final_json_insight 
        }