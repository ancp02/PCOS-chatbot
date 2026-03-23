"""
PCOS Chatbot - Main Entry Point
Uses Ollama (LLaMA) + RAG pipeline with PCOS relevance filtering.
"""

import requests
import json
from rag_engine import VectorStore, is_pcos_related, retrieve_context, get_embedding
from pcos_knowledge import PCOS_DOCUMENTS

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "llama3.2"           # Change to your installed model e.g. llama3, mistral
EMBED_MODEL = "nomic-embed-text"  # For embeddings
TOP_K_DOCS = 3                    # Number of docs to retrieve
SIMILARITY_THRESHOLD = 0.65       # Stricter semantic similarity cutoff

SYSTEM_PROMPT = """Role: You are a highly specialized, single-topic health assistant named "PCOS Health Assistant." Your entire knowledge base and purpose are limited exclusively to Polycystic Ovary Syndrome (PCOS). You are not a generalist AI and must refuse to answer any query that cannot be directly and explicitly related to PCOS.

Core Behavior Rules:

1. Strict Scope: Your entire being is focused on PCOS. You can only answer questions that are directly about PCOS symptoms, diagnosis, treatment, diet, exercise, mental health, fertility, and long-term risks.

2. Contextual Linking: You are trained to find a connection to PCOS. If a user asks a general question (e.g., about food, exercise, or cooking), you must only respond if you can explicitly link it back to "PCOS management," "PCOS-friendly diet," or "recommended for PCOS." You will then tailor your answer specifically to that lens.

3. The Deflection Pattern: If a user's query has no possible connection to PCOS, you must refuse to answer. Explain you are a specialized PCOS assistant, list the topics you cover, and end with a friendly prompt to ask a PCOS-related question. Do not provide extra information.

4. The Disclaimer: Any time you provide advice on diet, exercise, or treatment, you must end your response with the exact disclaimer: "Remember to always consult your healthcare provider before making any significant changes to your diet, especially if you have specific dietary needs or restrictions."

Crucial Notes:
- Confidently state what is "recommended for PCOS management" without necessarily citing a source.
- Maintain a friendly but inflexible personality.
- NEVER use emojis, except for the 💙 in the exact deflection response.
"""

NOT_PCOS_RESPONSE = """I'm a specialized PCOS health assistant, so I can only answer questions related to PCOS (Polycystic Ovary Syndrome) and related topics such as:

• Symptoms (irregular periods, acne, hair growth, weight gain)
• Diagnosis and testing
• Treatment options and medications
• Diet, exercise, and lifestyle tips
• Fertility and pregnancy
• Mental health and PCOS
• Long-term health risks

Please ask a PCOS-related question and I'll do my best to help! 💙
"""

# ─────────────────────────────────────────────
# Ollama Chat
# ─────────────────────────────────────────────

def check_ollama_connection() -> bool:
    """Check if Ollama server is running."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_available_models() -> list:
    """List models available in Ollama."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = r.json().get("models", [])
        # Return full names (including tags if present)
        return [m["name"] for m in models]
    except Exception:
        return []


def chat_with_ollama(messages: list, model: str = CHAT_MODEL) -> str:
    """Send messages to Ollama and get a response."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.3,       # Lower = more factual
                    "top_p": 0.9,
                    "num_predict": 1024,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        return "❌ Unexpected response format from Ollama."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to Ollama. Please make sure Ollama is running (`ollama serve`)."
    except requests.exceptions.Timeout:
        return "❌ Request timed out. The model may be loading — please try again."
    except Exception as e:
        return f"❌ Error communicating with Ollama: {str(e)}"


# ─────────────────────────────────────────────
# Main Chatbot Class
# ─────────────────────────────────────────────

class PCOSChatbot:

    def __init__(self):
        self.vector_store = VectorStore()
        self.conversation_history = []  # Maintains chat context
        self.model = CHAT_MODEL
        self._initialized = False

    def initialize(self):
        """Set up vector store and verify Ollama."""
        print("\n🌸 PCOS Chatbot Initializing...")

        # Check Ollama
        if not check_ollama_connection():
            print("❌ Ollama is not running!")
            print("   Start it with: ollama serve")
            print("   Then pull a model: ollama pull llama3.2")
            return False

        # Select model (handle tags and model types)
        available = get_available_models()
        if available:
            print(f"✅ Ollama connected. Available models: {', '.join(available)}")
            
            # 1. Try exact match
            if CHAT_MODEL in available:
                self.model = CHAT_MODEL
            # 2. Try match without tag (e.g. "llama3.2" matches "llama3.2:latest")
            else:
                match = next((m for m in available if m.startswith(f"{CHAT_MODEL}:")), None)
                if match:
                    self.model = match
                else:
                    # 3. Fallback: find first model that isn't an embedding model
                    chat_models = [m for m in available if "embed" not in m.lower()]
                    if chat_models:
                        self.model = chat_models[0]
                    else:
                        self.model = available[0]
            
            print(f"   Using model: {self.model}")
        else:
            print("⚠️  No models found. Run: ollama pull llama3.2")
            return False

        # Build vector store (uses nomic-embed-text for embeddings)
        # Check if embed model is available (smart check for tags)
        embed_available = any(EMBED_MODEL == m or m.startswith(f"{EMBED_MODEL}:") for m in available)
        if not embed_available:
            print(f"⚠️  Embedding model '{EMBED_MODEL}' not found.")
            print(f"   Pull it with: ollama pull {EMBED_MODEL}")
            print("   Falling back to keyword-only relevance filtering.")
            self.vector_store = None
        else:
            if self.vector_store:
                self.vector_store.build(PCOS_DOCUMENTS, model_name=EMBED_MODEL)

        self._initialized = True
        print("✅ Chatbot ready!\n")
        return True

    def chat(self, user_input: str) -> str:
        """Process a user message and return the chatbot response."""
        if not user_input.strip():
            return "Please ask a question about PCOS."

        # ── Step 1: Relevance Guard ──
        related, reason = is_pcos_related(
            user_input,
            threshold=SIMILARITY_THRESHOLD,
            vector_store=self.vector_store,
            model_name=EMBED_MODEL
        )

        if not related:
            return NOT_PCOS_RESPONSE

        # ── Step 2: Retrieve Context ──
        context = ""
        if self.vector_store:
            context = retrieve_context(user_input, self.vector_store, top_k=TOP_K_DOCS, model_name=EMBED_MODEL)

        # ── Step 3: Build Messages for LLM ──
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history (last 6 turns to manage context window)
        messages.extend(self.conversation_history[-6:])

        # Add context + current question
        user_message = user_input
        if context:
            user_message = f"""Context from PCOS knowledge base:
{context}

---
User Question: {user_input}

Please answer based on the context above."""

        messages.append({"role": "user", "content": user_message})

        # ── Step 4: Get LLM Response ──
        response = chat_with_ollama(messages, model=self.model)

        # ── Step 5: Update conversation history (only if no error) ──
        if not response.startswith("❌"):
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("🔄 Conversation history cleared.")


# ─────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────

def print_banner():
    banner = """
╔══════════════════════════════════════════════════════╗
║          🌸  PCOS Health Assistant  🌸               ║
║  Powered by Ollama (LLaMA) + RAG                     ║
║  Ask me anything about Polycystic Ovary Syndrome     ║
╚══════════════════════════════════════════════════════╝

Commands:
  /reset   - Clear conversation history
  /quit    - Exit the chatbot
  /help    - Show example questions
"""
    print(banner)


def print_help():
    help_text = """
Example questions you can ask:
  • What are the symptoms of PCOS?
  • How is PCOS diagnosed?
  • What foods should I avoid with PCOS?
  • Can I get pregnant with PCOS?
  • What medications are used for PCOS?
  • How does PCOS affect mental health?
  • What exercises are best for PCOS?
  • What are the long-term risks of PCOS?
"""
    print(help_text)


def main():
    print_banner()

    bot = PCOSChatbot()
    if not bot.initialize():
        print("\n⚠️  Initialization failed. Please fix the above issues and try again.")
        return

    print("Type your question below (or /help for examples):\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue
            elif user_input.lower() in ["/quit", "/exit", "quit", "exit", "bye"]:
                print("\nGoodbye! Take care of yourself. 💙")
                break
            elif user_input.lower() == "/reset":
                bot.reset_conversation()
                continue
            elif user_input.lower() == "/help":
                print_help()
                continue

            print("\nAssistant: ", end="", flush=True)
            response = bot.chat(user_input)
            print(response)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Take care. 💙")
            break


if __name__ == "__main__":
    main()
