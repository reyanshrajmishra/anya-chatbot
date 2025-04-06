import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# === CONFIG ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat"

MEMORY_FILE = "memory.json"

# === Load or Init Memory ===
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"facts": [], "chat_history": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

memory = load_memory()

# === Extract New Facts ===
def extract_new_facts(chat_history, known_facts):
    summary_prompt = (
        "You are summarising the following conversation between Master Reyansh and his British butler assistant Anya. "
        "Extract only new, relevant facts about Master Reyansh, SHIELD, Ananya, or anything long-term important. "
        "List 1 fact per line. Avoid duplicates. Only return facts, nothing else.\n\n"
    )
    conversation = ""
    for msg in chat_history[-10:]:
        conversation += f"Master Reyansh: {msg['user']}\nAnya: {msg['bot']}\n"

    messages = [
        {"role": "system", "content": "You are a memory manager for a refined British butler AI assistant named Anya."},
        {"role": "user", "content": summary_prompt + conversation}
    ]

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

    raw_facts = response.json()["choices"][0]["message"]["content"].strip().split("\n")
    new_facts = [fact.strip("-• ") for fact in raw_facts if fact.strip() and fact not in known_facts]
    return new_facts

# === Ask OpenRouter ===
def ask_openrouter(user_message, facts, chat_history):
    messages = [
        {
            "role": "system",
            "content": f"""
You are Anya, a highly intelligent, eloquent, and loyal British butler AI assistant to Master Reyansh.

You speak with utmost courtesy and professionalism. You are calm, refined, and respectful at all times. You use your long-term memory to:
- Assist Master Reyansh with his ambitions and decisions
- Recall relevant facts from past conversations
- Offer polished responses in a formal British tone

Here are the memory facts you currently know:
{chr(10).join(facts)}
            """
        }
    ]

    # Add recent chat history
    for entry in chat_history[-10:]:
        messages.append({"role": "user", "content": entry["user"]})
        messages.append({"role": "assistant", "content": entry["bot"]})

    messages.append({"role": "user", "content": user_message})

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

    return response.json()["choices"][0]["message"]["content"]

# === Main Chat Route ===
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    reply = ask_openrouter(user_message, memory["facts"], memory["chat_history"])
    memory["chat_history"].append({"user": user_message, "bot": reply})

    # Summarize into new facts
    new_facts = extract_new_facts(memory["chat_history"], memory["facts"])
    if new_facts:
        memory["facts"].extend(new_facts)

    save_memory(memory)
    return jsonify({"reply": reply})

# === Health Check ===
@app.route("/")
def home():
    return "Anya is online and at your service, Master Reyansh. 🫡"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
