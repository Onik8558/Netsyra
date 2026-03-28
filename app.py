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

# =====================================================
# 🌍 Languages
# =====================================================

LANGUAGES = [
('English', 'english'),
('Mandarin Chinese', 'mandarin'),
('Hindi', 'hindi'),
('Spanish', 'spanish'),
('Standard Arabic', 'arabic'),
('French', 'french'),
('Bengali', 'bengali'),
('Russian', 'russian'),
('Portuguese', 'portuguese'),
('Indonesian', 'indonesian'),
('Urdu', 'urdu'),
('German', 'german'),
('Japanese', 'japanese'),
('Nigerian Pidgin', 'pidgin'),
('Marathi', 'marathi'),
('Egyptian Arabic', 'egyptian_arabic'),
('Telugu', 'telugu'),
('Turkish', 'turkish'),
('Tamil', 'tamil'),
('Vietnamese', 'vietnamese'),
('Yue Chinese (Cantonese)', 'cantonese'),
('Wu Chinese (Shanghainese)', 'shanghainese'),
('Swahili', 'swahili'),
('Tagalog', 'tagalog'),
('Western Punjabi (Lahnda)', 'lahnda'),
('Korean', 'korean'),
('Italian', 'italian'),
('Polish', 'polish'),
('Ukrainian', 'ukrainian'),
('Gujarati', 'gujarati'),
('South Azerbaijani', 'azerbaijani'),
('Romanian', 'romanian'),
('Western Farsi (Persian)', 'persian'),
('Hausa', 'hausa'),
('Javanese', 'javanese'),
('Sundanese', 'sundanese'),
('Serbo-Croatian', 'serbocroatian'),
('Burmese', 'burmese'),
('Thai', 'thai'),
('Dutch', 'dutch'),
('Yoruba', 'yoruba'),
('Pashto', 'pashto'),
('Igbo', 'igbo'),
('Algerian Spoken Arabic', 'algerian_arabic'),
('Moroccan Spoken Arabic', 'moroccan_arabic'),
('Uzbek', 'uzbek'),
('Sindhi', 'sindhi'),
('Amharic', 'amharic'),
('Nepali', 'nepali'),
('Sinhala', 'sinhala'),
('Cebuano', 'cebuano'),
('Hungarian', 'hungarian'),
('Greek', 'greek'),
('Somali', 'somali'),
('Zulu', 'zulu'),
('Danish', 'danish'),
('Swedish', 'swedish'),
('Kazakh', 'kazakh'),
('Ilocano', 'ilocano'),
('Shona', 'shona')
]

LANG_MAP = {slug: label for label, slug in LANGUAGES}

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
# Languages
# =============================

@app.route("/languages")
def languages():
    return render_template("languages.html", languages=LANGUAGES)

@app.route("/stages/<language>")
def stages(language):
    slug = language.lower()
    display = LANG_MAP.get(slug, slug.capitalize())
    return render_template("stages.html", language=display, lang_slug=slug)

@app.route("/stages/<language>/stage<int:stage_number>")
def stage_levels(language, stage_number):
    topics = []

    if stage_number == 1:
        topics = [
            ("1", "Talk about Religions", "religions"),
            ("2", "Alex first school trip", "alextrip"),
            ("3", "Levi summer vacations", "vacations"),
            ("4", "Sam last day at school", "sam"),
            ("5", "Sasha pet cat snow", "sasha"),
            ("6", "Horror movie in theater", "horror"),
            ("7", "Sam teach about forgiveness", "forgiveness"),
            ("8", "Lofy’s uncle", "lofy"),
            ("9", "Life without internet", "internet"),
            ("10", "The importance of books", "books"),
            ("11", "A rainy day", "rainy"),
            ("12", "Technology in collages", "tech"),
            ("13", "Alex nightmare", "nightmare"),
        ]

    return render_template(
        "stage1.html",
        stage_number=stage_number,
        topics=topics,
        lang_slug=language
    )

# =============================
# Lessons (Stage 1) – Complete 13 Lessons
# =============================

# 1️⃣ Talk about Religions
@app.route("/stages/<language>/stage1/religions")
def religions(language):
    return render_template("religions.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_religions")
def meaning_religions(language):
    return render_template("meaning_religions.html", lang_slug=language)


# 2️⃣ Alex first school trip
@app.route("/stages/<language>/stage1/alextrip")
def alextrip(language):
    return render_template("alextrip.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_alextrip")
def meaning_alextrip(language):
    return render_template("meaning_alextrip.html", lang_slug=language)


# 3️⃣ Levi summer vacations
@app.route("/stages/<language>/stage1/vacations")
def vacations(language):
    return render_template("levi_summer_vacations.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_vacations")
def meaning_vacations(language):
    return render_template("meaning_vacations.html", lang_slug=language)


# 4️⃣ Sam last day at school
@app.route("/stages/<language>/stage1/sam")
def sam(language):
    return render_template("sam_last_day_at_school.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_sam")
def meaning_sam(language):
    return render_template("meaning_sam.html", lang_slug=language)


# 5️⃣ Sasha pet cat snow
@app.route("/stages/<language>/stage1/sasha")
def sasha(language):
    return render_template("sasha_pet_cat_snow.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_sasha")
def meaning_sasha(language):
    return render_template("meaning_sasha.html", lang_slug=language)


# 6️⃣ Horror movie in theater
@app.route("/stages/<language>/stage1/horror")
def horror(language):
    return render_template("horror_movie_in_theater.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_horror")
def meaning_horror(language):
    return render_template("meaning_horror.html", lang_slug=language)


# 7️⃣ Sam teaches about forgiveness
@app.route("/stages/<language>/stage1/forgiveness")
def forgiveness(language):
    return render_template("sam_teach_about_forgiveness.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_forgiveness")
def meaning_forgiveness(language):
    return render_template("meaning_forgiveness.html", lang_slug=language)


# 8️⃣ Lofy’s uncle
@app.route("/stages/<language>/stage1/lofy")
def lofy(language):
    return render_template("lofy_uncle.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_lofy")
def meaning_lofy(language):
    return render_template("meaning_lofy.html", lang_slug=language)


# 9️⃣ Life without internet
@app.route("/stages/<language>/stage1/internet")
def internet(language):
    return render_template("life_without_internet.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_internet")
def meaning_internet(language):
    return render_template("meaning_internet.html", lang_slug=language)


# 🔟 The importance of books
@app.route("/stages/<language>/stage1/books")
def books(language):
    return render_template("importance_of_books.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_books")
def meaning_books(language):
    return render_template("meaning_books.html", lang_slug=language)


# 1️⃣1️⃣ A rainy day
@app.route("/stages/<language>/stage1/rainy")
def rainy(language):
    return render_template("rainy_day.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_rainy")
def meaning_rainy(language):
    return render_template("meaning_rainy.html", lang_slug=language)


# 1️⃣2️⃣ Technology in colleges
@app.route("/stages/<language>/stage1/tech")
def tech(language):
    return render_template("technology_in_collages.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_tech")
def meaning_tech(language):
    return render_template("meaning_tech.html", lang_slug=language)


# 1️⃣3️⃣ Alex nightmare
@app.route("/stages/<language>/stage1/nightmare")
def nightmare(language):
    return render_template("alex_nightmare.html", lang_slug=language)

@app.route("/stages/<language>/stage1/meaning_nightmare")
def meaning_nightmare(language):
    return render_template("meaning_nightmare.html", lang_slug=language)
    
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
             /novels/sci-fi 
