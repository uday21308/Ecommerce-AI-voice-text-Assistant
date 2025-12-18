# 🛒 Ecommerce AI Voice Assistant

A real-time AI-powered ecommerce assistant that allows users to interact through **text and voice**, ask about products, check return policies, and track orders.

The system combines **Large Language Models (LLMs)**, **Retrieval-Augmented Generation (RAG)**, **browser-based speech interfaces**, and **backend decision logic** to deliver a complete conversational commerce experience.

---

## 📌 Project Overview

Voice-based interfaces are becoming a critical interaction channel in digital commerce.  
This project demonstrates an end-to-end AI voicebot capable of:

- Understanding spoken or typed customer queries  
- Answering ecommerce-related questions  
- Recommending products  
- Tracking orders using mock backend data  
- Responding with synthesized speech  
- Showing transparency via tool usage and retrieved context  

This implementation focuses on **clarity**, **modular design**, and **real-world ecommerce use cases**.

---

## 🎯 Key Features

- 🎤 Voice Interaction (Browser STT + TTS)  
- 💬 Text Chat Interface  
- 🧠 LLM-driven Conversational Intelligence  
- 📚 Retrieval-Augmented Generation (RAG)  
- 🛍️ Product Search & Recommendation  
- 📦 Order Tracking via Backend Logic  
- 🔍 Tool & Context Transparency Panel  
- 🧑‍💻 Modern UI (React + Tailwind CSS)  
- 🧩 Modular Backend Architecture  
- 📊 Observability-ready (LangSmith compatible)  

---

## 🏗️ System Architecture

### Voice / Text Interaction Flow
```markdown
User (Voice / Text)
      ↓
Browser Speech-to-Text (Web Speech API)
      ↓
FastAPI Backend
      ↓
Intent Router
   ├─ Small Talk → LLM
   ├─ Product Search → Tool + RAG
   ├─ Order Tracking → Mock Orders DB
      ↓
LLM Response (Groq)
      ↓
Text-to-Speech (Browser TTS)
      ↓
User hears response
```

### RAG Flow:
```markdown
User Query → Embed → Vector DB (Chroma)
           → Retrieve relevant products / FAQs
           → Inject into LLM prompt
```
---

## 🧩 Features Implemented

### ✅ Voice Interaction
- Browser-based Speech-to-Text  
- Browser-based Text-to-Speech  
- One-click microphone interaction  
- Automatic stop-speaking before listening  

### ✅ Conversational Intelligence
- LLM-powered reasoning (Groq – LLaMA 3.1)  
- System prompt enforcing ecommerce role  
- Small-talk handling  
- Graceful fallback for unsupported queries  

### ✅ Retrieval-Augmented Generation (RAG)
- Product catalog embeddings  
- FAQ & policy embeddings  
- Chroma vector database  
- Context grounding to reduce hallucinations  

### ✅ Backend Actions (Tools)
- 📦 Order tracking using mock `orders.csv`
- 🔄 Returns & refunds management using `returns.csv`
- 🛍️ Product search from structured catalog
- 🧠 Intent-based routing with safe fallbacks

### ✅ Observability
- LangSmith tracing enabled  
- Tracks:
  - LLM calls  
  - Retrieval steps  
  - Tool invocations  

### ✅ UI / UX
- Chat and voice in a single interface  
- Card-based professional UI (React + Tailwind)  
- Speaking avatar with waveform animation  
- Tool transparency panel  

---

## 🗂️ Project Structure

```markdown
Demo_Voicebot/
│
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── api.py               # API routes
│   ├── models.py            # Request/response models
│
├── ecommerce_llm.py         # Core LLM logic + intent routing
├── ragstore1.py             # RAG pipeline (Chroma + embeddings)
├── tools.py                 # Product search logic
├── orders.py                # Order lookup logic
├── products.csv             # Product catalog
├── orders.csv               # Mock order data
├── faqs.json                # FAQ / policy data
├── requirements.txt         # Backend dependencies
├── .env                     # Environment variables (not committed)
│
├── ecommerce-voice-ui/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── ToolPanel.jsx
│   │   │   ├── SpeakingWaveform.jsx
│   │   ├── utils/
│   │   │   ├── tts.js
│   │   ├── assets/
│   │   │   ├── bot_avatar.png
│   ├── index.html
│
└── README.md

```

---

## 🔊 Supported User Scenarios

### Informational Queries

“What is your return policy?”

### Product Queries
“Suggest watches under 5000”

### Order Tracking
“Track order ORD10008”

### Small Talk / Assistance
“Hi, can you help me?”

### Returns & Refunds
“Return order ORD10012 because of size issue”

### Order Placement
“Place an order for HANPOSH Men Watches”


## Demo and Test Cases
![WhatsApp Image 2025-12-18 at 11 59 06 AM](https://github.com/user-attachments/assets/baee200e-2d45-425e-8402-739c12b1367e)
![WhatsApp Image 2025-12-18 at 12 00 11 PM](https://github.com/user-attachments/assets/f8278020-6d21-4206-9581-a345d3d02d32)
![WhatsApp Image 2025-12-18 at 12 02 42 PM](https://github.com/user-attachments/assets/d4e47bd7-2a79-459e-8ba7-bc19b06afc15)
![WhatsApp Image 2025-12-18 at 12 04 20 PM](https://github.com/user-attachments/assets/e3c0553a-bab1-4717-8bb3-c31219a5c2f7)
![WhatsApp Image 2025-12-18 at 12 06 49 PM](https://github.com/user-attachments/assets/f453adf7-b5a5-47ac-975a-ebd784fc37b8)
![WhatsApp Image 2025-12-18 at 12 09 39 PM](https://github.com/user-attachments/assets/d2886ddc-1f66-4eab-b287-05e934a8d3e4)


---

## ⚙️ Setup Instructions

### 1️⃣ Backend Setup

```bash
cd Demo_Voicebot
python -m venv myenv
myenv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create .env file:
GROQ_API_KEY=your_groq_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=ecommerce-voicebot

Run backend:
```bash
uvicorn app.main:app --reload
```

Backend runs at:
http://127.0.0.1:8000

### 2️⃣ Frontend Setup
```bash
cd ecommerce-voice-ui
npm install
npm run dev
```
Frontend runs at:
http://localhost:5173


## 🙌 Conclusion

This project demonstrates a practical, modular, and extensible ecommerce voice assistant, showcasing real-world Generative AI concepts including LLMs, RAG, voice interaction, and observability — suitable for academic evaluation and further enhancement.
