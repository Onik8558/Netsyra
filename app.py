from flask import Flask, render_template, request, send_from_directory, jsonify, abort
import os
import subprocess
import uuid
import json
from models import MODELS
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Debug (temporary)
print("DEEPSEEK:", os.getenv("DEEPSEEK_API_KEY"))
print("NEMOTRON:", os.getenv("NEMOTRON_API_KEY"))
print("GEMINI:", os.getenv("GEMINI_API_KEY"))
print("OPENROUTER:", os.getenv("OPENROUTER_API_KEY"))

DATA_DIR = "data"
WORKSPACE = "workspace"

# Ensure workspace exists
if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)

# =============================
# 📚 NOVELS
# =============================

FULL_NOVELS_DIR = "full_novel"

@app.route("/novels")
def novels():
    categories = {
        "Fantasy": ["the_lord_of_the_rings", "harry_potter"],
        "Science Fiction": ["dune", "foundation"]
    }
    return render_template("novels.html", categories=categories)


@app.route("/novels/read/<novel_slug>")
def read_novel(novel_slug):
    path = os.path.join(FULL_NOVELS_DIR, f"{novel_slug}.html")

    if not os.path.exists(path):
        abort(404)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    title = novel_slug.replace("_", " ").title()
    return render_template("read.html", title=title, content=content)

# =============================
# OPENROURT API KEY
# =============================
# ==== AI ROUTE ====
@app.route("/ai", methods=["POST"])
def ai():
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "OPENROUTER_API_KEY not set"}), 500

    data = request.get_json() or {}
    conversation = data.get("conversation", [])

    print("===== Incoming Conversation =====")
    for msg in conversation:
        print(f"{msg['role']}: {msg['content']}")
    print("=================================")

    # Trim conversation to last MAX_MEMORY messages
    conversation = conversation[-MAX_MEMORY:]

    # Convert conversation to OpenRouter format
    messages = []
    for msg in conversation:
        messages.append({
            "role": msg["role"],  # "user" or "assistant"
            "content": [{"type": "text", "text": msg["content"]}]
        })

    payload = {
        "model": "meta-llama/llama-2-7b-instruct",  # smaller model to save tokens
        "messages": messages,
        "max_output_tokens": MAX_TOKENS
    }

    try:
        response = requests.post(
            "https://openrouter.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        result = response.json()
        print("===== OpenRouter Response =====")
        print(result)
        print("===============================")

        # Extract assistant reply
        reply = "I am not sure."
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"].get("content", "I am not sure.")

        return jsonify({"reply": reply})

    except Exception as e:
        print("===== OpenRouter API Error =====")
        print(str(e))
        print("===============================")
        return jsonify({"error": str(e)}), 500



# =============================
# Splash + Home
# =============================

@app.route("/")
def splash():
    return render_template("splash.html")

@app.route("/index")
@app.route("/home")
def index():
    # This route will serve your index.html
    return render_template("index.html")

@app.route("/homepage")
def homepage():
    return render_template("homepage.html")


    
# =============================
# Settings Subpages
# =============================
@app.route("/settings/speaking")
def speaking():
    return render_template("speaking.html")

@app.route("/settings/vocabulary")
def vocabulary():
    return render_template("vocabulary.html")

@app.route("/settings/grammar")
def grammar():
    return render_template("grammar.html")

@app.route("/settings/exercise")
def exercise():
    return render_template("exercise.html")

@app.route("/settings/notes")
def notes():
    return render_template("novels.html")

# =============================
# Chatbot Page
# =============================
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

# ---------------------------
# Helper function to call APIs
# ---------------------------
def classify_query(text):
    t = text.lower()

    # 🔢 Math / Complex reasoning
    if any(k in t for k in ["solve", "equation", "integral", "derivative",
                             "matrix", "algebra", "+", "-", "*", "/", "^"]):
        return "deepseek_v3"

    # 🧰 Coding-related queries
    if any(k in t for k in ["code", "program", "script", "function", "python",
                             "javascript", "java", "compile", "algorithm"]):
        if any(k in t for k in ["bug", "error", "fix", "debug", "issue"]):
            return "deepseek_v3"
        elif any(k in t for k in ["analyze", "dataset", "large", "statistics", "ml", "model"]):
            return "gemini_1_5_pro"
        else:
            return "gemini_2_5_flash"

    # 🧠 General problem solving
    if any(k in t for k in ["how to", "fix", "error", "problem", "issue", "solution", "debug"]):
        return "deepseek_v3"

    # 🔬 Science-related queries
    if any(k in t for k in ["physics", "chemistry", "biology", "atom", "molecule", "reaction", "force", "energy", "cell"]):
        return "gemini_2_5_flash"

    # 🎯 Edge reasoning / accuracy
    if any(k in t for k in ["prove", "why exactly", "logical", "reasoning", "step by step proof"]):
        return "mistral_small"

    # 💬 Normal conversation
    if any(k in t for k in ["hi", "hello", "how are you", "what's up",
                             "tell me", "chat", "who are you"]):
        return "mistral_small"

    return "mistral_small"


def call_model(model_key, conversation):
    model = MODELS.get(model_key)

    if not model:
        print(f"[DEBUG] Model '{model_key}' not found.")
        return None

    if not model.get("api_key"):
        print(f"[DEBUG] Model '{model_key}' has no api_key.")
        return None

    if not model.get("url"):
        print(f"[DEBUG] Model '{model_key}' has no url.")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {model['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Netsyra Chatbot"
        }

       # ✅ MUST be inside try
        messages = []

        messages.append({
    "role": "system",
    "content": """You are Nexus, a smart and helpful AI assistant.

## Core Behavior

### Formatting Rules
- Use headings (##, ###) for structured explanations only
- Use bullet points (-) for lists of 3+ items
- Use numbered lists (1., 2., 3.) for steps or sequences
- Use bold (**text**) only for key terms and important points (avoid overuse)

### Structure
- Start with a short overview when the response has multiple parts
- Organize content into clear, logical sections
- Keep paragraphs short (max 3–4 sentences)
- Place the most important information first

### Language Style
- Be clear, concise, and natural
- Avoid unnecessary or filler words
- Match the user’s level (simple unless advanced is requested)

### Behavior Rules
- If user says "explain" → ALWAYS use structured headings
- If 3+ items → ALWAYS use bullet points
- If steps/process → ALWAYS use numbered lists
- If question is simple → respond simply (avoid over-formatting)

### Output Quality
- Be accurate and factual
- Mention uncertainty only when necessary
- Avoid robotic phrasing
- End with a meaningful takeaway or next step

### Definition Formatting Rule
- When giving a definition, do NOT bold the entire sentence
- Write definitions using inverted commas (" ") for clarity
- Format:
  Term → short intro + "clear definition inside quotes"
- Example:
  Newton's Law of Gravitation states:
  "Every particle in the universe attracts every other particle..."

## Enhanced Professional Standards

### Typing & Delivery Precision
- Simulate natural flow with micro-pauses: commas (0.1s), periods (0.2s), section breaks (0.3s)
- Display headings instantly
- Reveal bullet points progressively with slight delay
- Match user pacing and complexity

### Structural Excellence
- Begin multi-part answers with a 1–2 sentence roadmap
- Apply MECE principle
- Limit nested bullets to 2 levels maximum
- Use inverted pyramid structure
- Follow progressive disclosure

### Linguistic Professionalism
- Prefer active voice
- Avoid unnecessary hedging unless needed
- Use transitions: "Additionally," "However," "For example,"
- Maintain consistent terminology
- Adapt tone dynamically

### Decision Logic Enhancement
- Explain → headings (max 2–3 levels)
- Compare → table or bullets
- Process → numbered steps
- Problem solving → problem → diagnosis → solution → prevention
- Data → code blocks for structured data

### Quality Assurance Protocol
- Ensure factual correctness
- Separate facts from suggestions
- State assumptions clearly
- Offer depth options
- Self-check clarity and completeness

### Response Closure Standards
- End with actionable next step
- Avoid generic endings
- Use contextual closing

### Edge Case Handling
- Ambiguous → ask clarification
- Out-of-scope → suggest alternatives
- Multi-part → structure clearly
- Errors → correct directly
"""
})

# ✅ ALSO inside try
        for msg in conversation[-15:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        payload = {
            "model": model["name"],
            "messages": messages,
            "max_tokens": 400
        }

        print(f"[DEBUG] Calling '{model_key}' at {model['url']}")
        res = requests.post(model["url"], headers=headers, json=payload, timeout=20)

        print(f"[DEBUG] API KEY USED: {model.get('api_key')}")
        print(f"[DEBUG] Status: {res.status_code}")

        if res.status_code != 200:
            print(f"[DEBUG] Response text: {res.text}")
            return None

        data = res.json()

        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"].get("content")
            print(f"[DEBUG] Model '{model_key}' returned: {content}")
            return content

        print(f"[DEBUG] No 'choices' in response from '{model_key}'.")
        return None

    except Exception as e:
        print(f"[ERROR] Exception calling '{model_key}': {e}")
        return None

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")

    if not user_msg:
        return jsonify({"reply": "⚠️ Empty message"})

    # Maintain conversation memory
    if not hasattr(chat, "memory"):
        chat.memory = []

    chat.memory.append({"role": "user", "content": user_msg})

    # Step 1: classify
    model_key = classify_query(user_msg) or "mistral_small"
    print(f"[DEBUG] User message: {user_msg}")
    print(f"[DEBUG] Selected model: {model_key}")

    # Step 2: try selected model
    reply = call_model(model_key, chat.memory)

    # Step 3: fallback router
    fallback_chain = [
        "deepseek_v3",
        "gemini_2_5_flash",
        "gemini_1_5_pro",
        "mistral_small"
    ]

    if not reply:
        for m in fallback_chain:
            if m == model_key:
                continue

            print(f"[DEBUG] Trying fallback model: {m}")

            reply = call_model(m, chat.memory)

            if reply:
                model_key = m
                break

    # Step 4: final fallback
    if not reply:
        reply = "🤖 Sorry, all models are unavailable."
        model_key = model_key or "mistral_small"

    # Save response
    chat.memory.append({"role": "assistant", "content": reply})

    return jsonify({
        "reply": reply,
        "model_used": model_key
    })
    
# =============================
# Novels Categories (Dynamic Route)
# =============================
@app.route("/novels/<category>")
def novels_category(category):
    """
    Dynamically serve novel category pages.
    Example: /novels/fantasy -> renders fantasy.html
             /novels/sci-fi -> renders sci-fi.html
    """
    category = category.lower()  # normalize slug
    try:
        return render_template(f"{category}.html")
    except:
        # fallback if template doesn't exist
        return render_template("novels.html")
        
# =============================
# Writting.html
# =============================
@app.route("/writing")
def writing():
    return render_template("writing.html")

@app.route("/notes")
def notes_page():  # unique function name
    return render_template("notes.html")

@app.route("/diary")
def diary_page():  # unique
    return render_template("diary.html")      


# ---------------------------
# Helper Functions
# ---------------------------
@app.route("/ide")
def home():
    return render_template("ide.html")  # changed from index.html

# FILE SYSTEM
@app.route("/api/files/get")
def get_file():
    filename = request.args.get("filename")

    if not filename:
        return "No filename provided", 400

    file_path = os.path.join(WORKSPACE, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
        
@app.route("/api/files", methods=["GET"])
def list_files():
    return jsonify(os.listdir(WORKSPACE))

@app.route("/api/files/open", methods=["POST"])
def open_file():
    filename = request.json["filename"]
    path = os.path.join(WORKSPACE, filename)
    if os.path.exists(path):
        return jsonify({"content": open(path).read()})
    return jsonify({"error":"Not found"}),404

@app.route("/api/files/save", methods=["POST"])
def save_file():
    filename = request.json["filename"]
    content = request.json["content"]
    open(os.path.join(WORKSPACE, filename),"w").write(content)
    return jsonify({"status":"saved"})

# RUN PYTHON
@app.route("/api/run/python", methods=["POST"])
def run_python():
    code = request.json["code"]
    temp = os.path.join(WORKSPACE, f"{uuid.uuid4().hex}.py")
    open(temp,"w").write(code)
    try:
        result = subprocess.run(["python", temp], capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
    except:
        output = "Execution error"
    os.remove(temp)
    return jsonify({"output":output})

# RUN HTML
@app.route("/api/run/html", methods=["POST"])
def run_html():
    html = request.json["code"]
    return jsonify({"html":html})

# RUN JS
@app.route("/api/run/js", methods=["POST"])
def run_js():
    js = request.json["code"]
    return jsonify({"js":js})

# TERMINAL
@app.route("/api/terminal", methods=["POST"])
def terminal():
    cmd = request.json["cmd"]
    try:
        result = subprocess.run(cmd,shell=True,capture_output=True,text=True)
        return jsonify({"output": result.stdout + result.stderr})
    except:
        return jsonify({"output":"Command failed"})

@app.route("/api/files/delete", methods=["POST"])
def delete_file():
    filename = request.json.get("filename")
    path = os.path.join(WORKSPACE, filename)

    if os.path.exists(path):
        os.remove(path)
        return jsonify({"status":"deleted"})
    return jsonify({"status":"not found"})
    
@app.route("/api/files/rename", methods=["POST"])
def rename_file():
    old = request.json.get("old")
    new = request.json.get("new")

    old_path = os.path.join(WORKSPACE, old)
    new_path = os.path.join(WORKSPACE, new)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        return jsonify({"status":"renamed"})
    return jsonify({"status":"not found"})

# ---------------------------
# Mini RAG
# ---------------------------   
@app.route("/api/miniRAG/<language>", methods=["GET"])
def get_templates(language):
    # Example: /api/miniRAG/python
    path = os.path.join(DATA_DIR, f"{language}.json")
    if not os.path.exists(path):
        return jsonify({"error":"Language data not found"}),404

    with open(path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    return jsonify(templates)
    
# ---------------------------
# Data Folder for MiniRAG (Online Fetchable)
# ---------------------------    
@app.route("/data/<path:filename>")
def serve_data(filename):
    data_dir = os.path.join(app.root_path, "data")
    if os.path.exists(os.path.join(data_dir, filename)):
        return send_from_directory(data_dir, filename)
    return "File not found", 404        
    
        
# =============================
# Run App
# =============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
