"""
RAG Engine for PCOS Chatbot
Handles: embedding, vector store (in-memory FAISS), retrieval, relevance filtering
"""

import os
import json
import numpy as np
from typing import List, Tuple, Optional
from pcos_knowledge import PCOS_DOCUMENTS, PCOS_KEYWORDS_STRONG, PCOS_KEYWORDS_RELATED


# ─────────────────────────────────────────────
# Embedding via Ollama (nomic-embed-text model)
# ─────────────────────────────────────────────

def get_embedding(text: str, model: str = "nomic-embed-text", task: Optional[str] = None) -> List[float]:
    """Get embedding from Ollama embedding model with optimal prefixes."""
    import requests
    
    # Apply nomic-specific prefixes if needed
    processed_text = text
    if model.startswith("nomic-embed-text") and task:
        if task == "search_query":
            processed_text = f"search_query: {text}"
        elif task == "search_document":
            processed_text = f"search_document: {text}"

    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": processed_text},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if "embedding" in data:
            return data["embedding"]
        print(f"[Embedding Error] No 'embedding' key in response from Ollama: {data}")
        return []
    except Exception as e:
        print(f"[Embedding Error] {e}")
        return []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    vec_a, vec_b = np.array(a), np.array(b)
    if np.linalg.norm(vec_a) == 0 or np.linalg.norm(vec_b) == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)))


# ─────────────────────────────────────────────
# In-Memory Vector Store
# ─────────────────────────────────────────────

class VectorStore:
    """Simple in-memory vector store."""

    CACHE_FILE = "vector_cache.json"

    def __init__(self):
        self.documents = []       # List of doc dicts
        self.embeddings = []      # List of embedding vectors

    def build(self, docs: List[dict], embed_fn=get_embedding, model_name: str = "nomic-embed-text"):
        """Build the vector store from documents."""
        print(f"Building vector store (model: {model_name})...")

        # Try loading from cache first
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r") as f:
                    cache = json.load(f)
                
                # Verify cache was built with same model
                if cache.get("model") == model_name:
                    print("Loading embeddings from cache...")
                    self.documents = cache["documents"]
                    self.embeddings = cache["embeddings"]
                    print(f"Loaded {len(self.documents)} docs from cache.")
                    return
                else:
                    print(f"Cache was built with different model ({cache.get('model')}). Rebuilding...")
            except Exception as e:
                print(f"Error loading cache: {e}. Rebuilding...")

        # Build fresh embeddings
        for doc in docs:
            text = f"{doc['topic']}. {doc['content']}"
            embedding = embed_fn(text, model=model_name, task="search_document")
            if embedding:
                self.documents.append(doc)
                self.embeddings.append(embedding)
                print(f"  Embedded: {doc['topic']}")

        # Save to cache
        with open(self.CACHE_FILE, "w") as f:
            json.dump({
                "model": model_name,
                "documents": self.documents, 
                "embeddings": self.embeddings
            }, f)
        print(f"Vector store built with {len(self.documents)} documents.")

    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[dict, float]]:
        """Return top-k most similar documents."""
        if not self.embeddings:
            return []
        scores = [cosine_similarity(query_embedding, emb) for emb in self.embeddings]
        ranked = sorted(zip(self.documents, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# ─────────────────────────────────────────────
# PCOS Relevance Guard
# ─────────────────────────────────────────────

def is_pcos_related(query: str, threshold: float = 0.65,
                    vector_store: Optional[VectorStore] = None,
                    embed_fn=get_embedding, model_name: str = "nomic-embed-text") -> Tuple[bool, str]:
    """
    Three-layer relevance check:
    1. Strong keyword scan (PCOS-specific terms).
    2. Related keyword + High semantic similarity.
    3. Pure semantic similarity (requires VERY high score ~0.75+).
    """
    query_lower = query.lower()

    # Layer 1: Strong Keyword match (Immediate pass)
    strong_matches = [kw for kw in PCOS_KEYWORDS_STRONG if kw in query_lower]
    if strong_matches:
        return True, f"Strong keyword match: {strong_matches[:2]}"

    # Layer 2: Related Keyword check
    related_matches = [kw for kw in PCOS_KEYWORDS_RELATED if kw in query_lower]
    
    # Get semantic similarity for subsequent layers
    score = 0.0
    if vector_store and vector_store.embeddings:
        query_emb = embed_fn(query, model=model_name, task="search_query")
        if query_emb:
            results = vector_store.search(query_emb, top_k=1)
            if results:
                _, score = results[0]

    # Layer 2 Pass: Related keyword + high semantic similarity
    if related_matches and score >= threshold:
        return True, f"Related word ({related_matches[0]}) + Score: {score:.2f}"

    # Layer 3 Pass: Very high semantic score ONLY (no keywords required, but must be near-perfect)
    # Require ~0.75+ for semantic-only match (much stricter than threshold)
    if score >= 0.75:
        return True, f"High semantic score: {score:.2f}"

    return False, f"No strong connection (Score: {score:.2f})"


# ─────────────────────────────────────────────
# Context Retrieval
# ─────────────────────────────────────────────

def retrieve_context(query: str, vector_store: VectorStore,
                     top_k: int = 3, embed_fn=get_embedding, model_name: str = "nomic-embed-text") -> str:
    """Retrieve and format relevant PCOS context for the query."""
    query_emb = embed_fn(query, model=model_name, task="search_query")
    if not query_emb:
        return ""

    results = vector_store.search(query_emb, top_k=top_k)
    if not results:
        return ""

    context_parts = []
    for doc, score in results:
        context_parts.append(
            f"### {doc['topic']} (relevance: {score:.2f})\n{doc['content'].strip()}"
        )

    return "\n\n".join(context_parts)
