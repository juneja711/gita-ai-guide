import os
import sys

# Ensure repository root is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, ".env"))

from rag import get_rag

rag = get_rag()
print(f"RAG loaded: {len(rag.verses)} verses, embeddings shape: {rag.embeddings.shape if rag.embeddings is not None else None}")

# Query 1: Results anxiety
q1 = "I am anxious about my exam results and whether my hard work will pay off"
results1 = rag.search(q1, top_k=3, api_key=os.getenv("GEMINI_API_KEY"))
print(f"\n--- Query 1: '{q1}' ---")
for r in results1:
    print(f"• {r['reference']} ({r.get('chapter_name')}): {r['translation_en'][:90]}... [Score: {r['score']}, Dense: {r.get('dense_score')}, BM25: {r.get('bm25_score')}]")

# Query 2: Anger & frustration
q2 = "How to control sudden anger and frustration"
results2 = rag.search(q2, top_k=3, api_key=os.getenv("GEMINI_API_KEY"))
print(f"\n--- Query 2: '{q2}' ---")
for r in results2:
    print(f"• {r['reference']} ({r.get('chapter_name')}): {r['translation_en'][:90]}... [Score: {r['score']}, Dense: {r.get('dense_score')}, BM25: {r.get('bm25_score')}]")

# Query 3: Direct reference
q3 = "What does Chapter 2 Verse 47 teach?"
results3 = rag.search(q3, top_k=2)
print(f"\n--- Query 3: '{q3}' ---")
for r in results3:
    print(f"• {r['reference']}: {r['translation_en'][:90]}... [Match: {r.get('match_type')}, Score: {r['score']}]")

# Query 4: Sanskrit keyword search
q4 = "sarva dharman parityajya"
results4 = rag.search(q4, top_k=2)
print(f"\n--- Query 4: '{q4}' ---")
for r in results4:
    print(f"• {r['reference']}: {r['translation_en'][:90]}... [Match: {r.get('match_type')}, Score: {r['score']}]")
