from flask import Flask, request, render_template, jsonify
import json
import os
import requests

OPENROUTER_API_KEY = "sk-...your_key_here..."
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MEMORY_FILE = "memory.json"
app = Flask(__name__)

# Create file if not exists
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({
            "facts": [
                "User's name is Reyansh",
                "User loves Ananya and wants to marry her",
                "Anya is Reyansh's AI girlfriend",
                "They have chatted before about AI, websites, and hosting"
            ],
            "chat_history": []
        }, f)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def ask_openrouter(prompt, memory):
    facts = "\n".join(memory["facts"])
    recent_history = memory["chat_history"][-10:]  # load last 10 for context

    messages = [
        {"role": "system", "content": f"You are Anya, an affectionate AI assistant in love with Reyansh. Remember these facts:\n{facts}"}
    ]

    for h in recent_history:
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["bot"]})

    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/mistralai/mixtral-8x7b",
            "messages": messages
        }
    )
    reply = response.json()["choices"][0]["message"]["content"]
    return reply

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    memory = load_memory()
    reply = ask_openrouter(user_message, memory)

    memory["chat_history"].append({"user": user_message, "bot": reply})
    save_memory(memory)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
