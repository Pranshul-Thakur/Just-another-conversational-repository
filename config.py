# Filename: config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration management."""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Model Settings
    MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
    
    # System Prompts
    SYSTEM_INSTRUCTION = """
    You are a helpful and empathetic conversational assistant. 
    For every user input, you must perform two tasks:
    1. Analyze the sentiment of the user's message (Positive, Negative, or Neutral) and assign a score (-1.0 to 1.0).
    2. Generate a helpful, natural response.
    
    You MUST return your answer in strict JSON format:
    {
        "sentiment_label": "Positive" | "Negative" | "Neutral",
        "sentiment_score": float, 
        "reply": "string"
    }
    """
    
    # Thresholds
    SENTIMENT_THRESHOLD_POSITIVE = 0.1
    SENTIMENT_THRESHOLD_NEGATIVE = -0.1
    
    # Retry Logic
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # Seconds