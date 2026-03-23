import sys
from rag_engine import is_pcos_related, VectorStore, get_embedding
from pcos_knowledge import PCOS_DOCUMENTS

vs = VectorStore()
vs.build(PCOS_DOCUMENTS, model_name="nomic-embed-text")

queries = ["what is constipation", "how do I cook chicken", "what is PCOS", "symptoms of pcos", "my hormones are imbalanced", "I have pain in my lower stomach", "how to cure acne"]
for q in queries:
    related, reason = is_pcos_related(q, threshold=0.65, vector_store=vs, model_name="nomic-embed-text")
    print(f"Query: '{q}'\nRelated: {related}\nReason: {reason}\n")
