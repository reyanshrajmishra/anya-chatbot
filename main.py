from flask import Flask, render_template, request, jsonify
import json
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
MEMORY_FILE = "memory.json"

# Ensure memory exists
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"chat_history": []}, f)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)

def search_google(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(f"https://www.google.com/search?q={query}", headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select("div.tF2Cxc")
    links = []
    for r in results[:3]:
        title = r.select_one("h3").text if r.select_one("h3") else "No title"
        url = r.select_one("a")["href"]
        links.append(f"{title}:\n{url}")
    return "\n\n".join(links) if links else "No results found."

def basic_ai_reply(message, memory):
    if "how are you" in message.lower():
        return "I'm doing great, thanks for asking! 😊"
    if "your name" in message.lower():
        return "My name is Anya, your personal AI assistant 💖"
    if "love" in message.lower():
        return "Aww, love is beautiful. Tell me more about how you feel. 💌"
    if "hi" in message.lower() or "hello" in message.lower():
        return "Hey there! 😊 What’s up?"
    if "?" in message:
        return "That's an interesting question. I’ll remember it!"
    # Default
    return f"I remember you said: \"{memory[-1]}\""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    data = load_memory()
    history = data.get("chat_history", [])

    if user_input.lower().startswith("search:"):
        query = user_input[7:].strip()
        reply = search_google(query)
    else:
        reply = basic_ai_reply(user_input, history)

    # Save memory
    history.append(user_input)
    data["chat_history"] = history[-50:]  # Keep last 50 messages only
    save_memory(data)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
