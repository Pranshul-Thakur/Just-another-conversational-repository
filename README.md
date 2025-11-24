# Sentiment Analysis Chatbot

A full-stack conversational AI application that performs real-time sentiment analysis, emotion detection, and executive reporting. Built with **Python (Flask)** and powered by **Google Gemini 2.5**.

## Key Features

### Advanced Sentiment Engine
* **Hybrid Architecture:** Combines Large Language Models (Gemini) for semantic understanding with deterministic Python heuristics for intensity detection.
* **Multi-Dimensional Analysis:**
    * **Polarity:** Positive / Negative / Neutral.
    * **Emotion Classification:** Detects specific states like *Joy, Anger, Confusion, Fear*.
    * **Intensity Logic:** Automatically detects shouting (ALL CAPS) or profanity to amplify/penalize scores.

### Analytics & Reporting
* **Executive Summaries:** Generates a qualitative, human-like summary of the conversation flow (e.g., *"The user started frustrated but left happy due to quick resolution"*).
* **Trend Detection:** Mathematically compares the first half of the chat vs. the second half to flag if the mood is **Improving** or **Declining**.
* **Audit Exports:** Download detailed session reports in **JSON** or **TXT** formats for external auditing.

### Persistence & UX
* **Session Management:** Create multiple chat sessions, stored persistently in a **SQLite** database.
* **Inline Editing:** Rename chat sessions directly in the sidebar.
* **Review Mode:** A dedicated "Analyst View" that overlays sentiment metadata on the chat history without cluttering the user experience during the conversation.

---

## Technical Architecture

### Why SQLite instead of Vector DB?
For the chat history feature, we chose a Relational Database (**SQLite**) over a Vector Database.
* **Requirement:** Exact retrieval of a specific session by ID in chronological order.
* **Reasoning:** Vector DBs are optimized for *semantic similarity search* (RAG), which introduces overhead and latency. SQL provides O(1) lookup speed and guarantees data integrity for session management.

### The Scoring Algorithm
The final sentiment score is calculated using a weighted formula:
$$S_{final} = \text{clamp}\left( (S_{base} \cdot (1 + 0.5I)) - (0.4 \cdot P) , -1.0, 1.0 \right)$$
* **$S_{base}$**: Semantic score from Gemini LLM.
* **$I$ (Intensity)**: 1.5x multiplier if user is shouting (>60% Uppercase).
* **$P$ (Profanity)**: Flat -0.4 penalty per swear word found.

---

## Installation

### Prerequisites
* Python 3.8+
* Google Gemini API Key

### 1. Clone & Setup
```bash
# Install dependencies
pip install flask google-generativeai python-dotenv
```

### 2. Configuration

Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Run the Application

```bash
python main.py
```

The application will start at `http://127.0.0.1:5000`.

## Project Structure

```
/project-root
│
├── main.py             # Flask API & Routes (The Controller)
├── gemini_bot.py       # AI Logic, Heuristics & Scoring (The Service)
├── database.py         # SQLite Persistence Layer (The Model)
├── config.py           # Constants & Environment Variables
├── .env                # Secrets (Not committed to Git)
│
├── data/
│   └── chat_history.db # Persistent storage (Created automatically)
│
└── templates/
    └── index.html      # Single-page Frontend (HTML/CSS/JS)
```

## Innovation Points (Bonus)

1. **Safety Nets:** The system doesn't blindly trust the AI. If a user types "I HATE THIS," the Python heuristic overrides any potential AI hallucination to ensure it is flagged as Anger.
2. **JSON Guardrails:** The backend validates the structure of every AI response. If the LLM returns malformed data, the system gracefully degrades to a fallback state without crashing.
3. **Zero-Footprint Exports:** Reports (JSON/TXT) are generated entirely in-memory using Python's `io` module. This allows users to download detailed audit logs without creating temporary files on the server, preventing disk bloat and I/O bottlenecks.