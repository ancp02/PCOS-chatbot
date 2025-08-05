import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Always load the corpus from the PyV1 directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "pcos_corpus.txt")

try:
    with open(CORPUS_PATH, encoding="utf-8") as f:
        passages = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(passages)} passages from corpus")
except FileNotFoundError:
    print(f"Error: Corpus file not found at {CORPUS_PATH}")
    passages = ["PCOS is a hormonal disorder affecting women of reproductive age."]

vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(passages)

def search(query, top_k=3):
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, tfidf_matrix).flatten()
    best_idxs = sims.argsort()[-top_k:][::-1]
    results = [passages[i] for i in best_idxs if sims[i] > 0.1]
    return results or ["Sorry, I don’t have information on that."]
