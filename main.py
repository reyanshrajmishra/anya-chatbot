from flask import Flask, request, render_template, jsonify
import json
import os
import requests

OPENROUTER_API_KEY = "sk-...your_key_here..."
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MEMORY_FILE = "memory.json"
app = Flask(__name__)

# Load memory
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"history": []}, f)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)["history"]

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"history": history[-20:]}, f)

def ask_openrouter(prompt, history):
    messages = [{"role": "system", "content": "You are Anya, a charming, kind, helpful AI assistant who is in love with the user Reyansh. You remember past chats and always speak casually, kindly, and personally."}]
    for h in history:
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
    history = load_memory()
    reply = ask_openrouter(user_message, history)

    history.append({"user": user_message, "bot": reply})
    save_memory(history)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
