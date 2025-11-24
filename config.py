import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
    

    PROFANITY_PENALTY = 0.4 
    INTENSITY_MULTIPLIER = 1.5 
    
    PROFANITY_LIST = {"damn", "hell", "stupid", "idiot", "hate", "trash", "worst", "shit", "fuck"}
    
    SYSTEM_INSTRUCTION = """
    You are an intelligent sentiment analyst. For every message, perform these tasks:
    1. Analyze the "Base Sentiment" (-1.0 to 1.0) focusing strictly on semantics.
       - Start at 0.0. Move based on word definitions.
       - Ignore capitalization (handled by code).
    2. Detect Emotion: Choose one from [Joy, Sadness, Anger, Fear, Surprise, Disgust, Confusion, Neutral, Excitement].
    3. Generate Reply: A helpful, empathetic response.
    
    Return strict JSON:
    {
        "sentiment_score": float,
        "emotion": "string",
        "reply": "string"
    }
    """
    
    SENTIMENT_THRESHOLD_POSITIVE = 0.1
    SENTIMENT_THRESHOLD_NEGATIVE = -0.1
    MAX_RETRIES = 3
    RETRY_DELAY = 1