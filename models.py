# models.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🌟 Use ONE API key (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ===============================
# Model definitions (WORKING)
# ===============================
MODELS = {
    # 🧠 DeepSeek (fast + smart)
    "deepseek_v3": {
        "name": "deepseek/deepseek-chat",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": OPENROUTER_API_KEY
    },

    # ⚡ Fast lightweight (Gemma via OpenRouter)
    "gemini_2_5_flash": {
        "name": "google/gemma-7b-it",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": OPENROUTER_API_KEY
    },

    # 🧠 Balanced reasoning
    "gemini_1_5_pro": {
        "name": "google/gemma-7b-it",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": OPENROUTER_API_KEY
    },

    # 📘 Stable fallback (Mistral)
    "mistral_small": {
        "name": "mistralai/mistral-7b-instruct",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": OPENROUTER_API_KEY
    }
}
