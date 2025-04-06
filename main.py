from flask import Flask, render_template, request, jsonify
import json
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
MEMORY_FILE = "memory.json"

# Load or create memory
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({}, f)

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
        title = r.select_one("h3").text
        url = r.select_one("a")["href"]
        links.append(f"{title}: {url}")
    return "\n".join(links) if links else "No results found."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = load_memory()
    msg = request.json.get("message", "")
    if msg.startswith("search:"):
        query = msg.replace("search:", "").strip()
        reply = search_google(query)
    else:
        memory = data.get("memory", [])
        reply = f"Anya remembers this chat: {memory[-1] if memory else 'nothing yet.'}"
        memory.append(msg)
        data["memory"] = memory
        save_memory(data)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
