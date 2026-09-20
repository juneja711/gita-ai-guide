"""
Gita AI Guide - Core Retrieval-Augmented Generation (RAG) Engine
Combines:
1. Exact Scripture Reference Parsing (e.g. Chapter 2 Verse 47, 2:47, BG 18.66)
2. Semantic Dense Vector Search (gemini-embedding-001 with precomputed 701-verse index)
3. Lexical / BM25 Keyword Search (Sanskrit transliteration, English keywords, Chapter themes)
4. Hybrid Fusion & LLM Grounding Context Construction
5. Zero-Failure Graceful Fallback (if API is unreachable, BM25 operates 100% offline)
"""

import os
import re
import math
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None

class GitaRAG:
    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
        
        self.data_dir = data_dir
        self.verses: List[Dict[str, Any]] = []
        self.verses_by_ref: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.verses_by_id: Dict[int, Dict[str, Any]] = {}
        self.chapters: List[Dict[str, Any]] = []
        
        self.embeddings: Optional[Any] = None # np.ndarray if loaded
        self.embedding_ids: List[int] = []
        self.embedding_id_to_idx: Dict[int, int] = {}

        # BM25 index data structures
        self.corpus_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {} # Document frequency per term
        self.idf: Dict[str, float] = {}

        self._load_data()
        self._load_embeddings()
        self._build_bm25_index()

    def _load_data(self):
        verses_path = os.path.join(self.data_dir, "gita_verses.json")
        chapters_path = os.path.join(self.data_dir, "chapters.json")

        if os.path.exists(verses_path):
            try:
                with open(verses_path, "r", encoding="utf-8") as f:
                    self.verses = json.load(f)
                for v in self.verses:
                    ch = v.get("chapter", 0)
                    verse = v.get("verse", 0)
                    vid = v.get("id", 0)
                    self.verses_by_ref[(ch, verse)] = v
                    self.verses_by_id[vid] = v
            except Exception as e:
                print(f"[GitaRAG] Error loading verses: {e}")

        if os.path.exists(chapters_path):
            try:
                with open(chapters_path, "r", encoding="utf-8") as f:
                    self.chapters = json.load(f)
            except Exception as e:
                print(f"[GitaRAG] Error loading chapters: {e}")

    def _load_embeddings(self):
        if np is None:
            print("[GitaRAG] numpy is not installed, running in pure lexical/BM25 mode.")
            return

        emb_path = os.path.join(self.data_dir, "gita_embeddings.npz")
        if os.path.exists(emb_path):
            try:
                data = np.load(emb_path)
                self.embeddings = data["embeddings"] # normalized float32 matrix (N, D)
                self.embedding_ids = list(data["ids"])
                self.embedding_id_to_idx = {vid: idx for idx, vid in enumerate(self.embedding_ids)}
                print(f"[GitaRAG] Loaded dense vector index: {self.embeddings.shape} across {len(self.embedding_ids)} verses.")
            except Exception as e:
                print(f"[GitaRAG] Error loading embeddings from {emb_path}: {e}")

    def reload_embeddings(self):
        """Allows hot-reloading embeddings once generation finishes."""
        self._load_embeddings()

    # --- BM25 Tokenizer & Indexer ---
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [w for w in cleaned.split() if len(w) > 2]
        return tokens

    def _build_bm25_index(self):
        if not self.verses:
            return

        self.corpus_tokens = []
        self.doc_lengths = []
        self.df = {}
        total_len = 0

        for v in self.verses:
            # Aggregate textual features: transliteration, translation, keywords, chapter name
            doc_text = (
                f"{v.get('chapter_name', '')} {v.get('chapter_meaning', '')} "
                f"{v.get('transliteration', '')} {v.get('translation_en', '')} "
                f"{v.get('word_meanings', '')} {v.get('reference', '')}"
            )
            tokens = self._tokenize(doc_text)
            self.corpus_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            # Track document frequency
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] = self.df.get(t, 0) + 1

        num_docs = len(self.verses)
        self.avg_doc_len = total_len / max(num_docs, 1)

        # Precompute IDF (Robertson-Spärck Jones)
        self.idf = {}
        for t, count in self.df.items():
            self.idf[t] = math.log((num_docs - count + 0.5) / (count + 0.5) + 1.0)

    def _bm25_scores(self, query: str) -> List[float]:
        q_tokens = self._tokenize(query)
        num_docs = len(self.verses)
        scores = [0.0] * num_docs
        if not q_tokens or not self.corpus_tokens:
            return scores

        k1 = 1.5
        b = 0.75

        for t in q_tokens:
            if t not in self.idf:
                continue
            t_idf = self.idf[t]
            for doc_idx, doc in enumerate(self.corpus_tokens):
                tf = doc.count(t)
                if tf > 0:
                    doc_len = self.doc_lengths[doc_idx]
                    denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    scores[doc_idx] += t_idf * ((tf * (k1 + 1.0)) / denom)

        return scores

    # --- Query Embedding Helper ---
    def _embed_query(self, query: str, api_key: str) -> Optional[List[float]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
        payload = {
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": query}]}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("embedding", {}).get("values")
        except Exception as e:
            print(f"[GitaRAG] Query embedding error (fallback will activate): {e}")
            return None

    # --- Scripture Reference Parser ---
    @staticmethod
    def parse_direct_reference(query: str) -> Optional[Tuple[int, int]]:
        """Detects patterns like 'Chapter 2 Verse 47', 'chapter 2, verse 47', '2:47', '2.47', 'BG 18.66'"""
        q = query.strip()
        
        # Pattern 1: Chapter X Verse Y
        m = re.search(r"(?:chapter|ch\.?)\s*([1-9]|1[0-8])\s*[,.:\-]?\s*(?:verse|sloka|shloka|v\.?)?\s*([1-9][0-9]?)", q, re.IGNORECASE)
        if m:
            ch, v = int(m.group(1)), int(m.group(2))
            if 1 <= ch <= 18 and 1 <= v <= 78:
                return (ch, v)

        # Pattern 2: BG X.Y or Gita X:Y or X:Y or X.Y
        m2 = re.search(r"(?:bg|gita)?\s*\b([1-9]|1[0-8])\s*[:.]\s*([1-9][0-9]?)\b", q, re.IGNORECASE)
        if m2:
            ch, v = int(m2.group(1)), int(m2.group(2))
            if 1 <= ch <= 18 and 1 <= v <= 78:
                return (ch, v)

        return None

    # --- Hybrid Search ---
    def search(
        self,
        query: str,
        top_k: int = 3,
        api_key: Optional[str] = None,
        dense_weight: float = 0.75,
        sparse_weight: float = 0.25
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant Gita verses for the query.
        Returns a list of dicts with verse metadata and match scores.
        """
        if not self.verses:
            return []

        # 1. Exact reference check
        direct_ref = self.parse_direct_reference(query)
        if direct_ref and direct_ref in self.verses_by_ref:
            exact_verse = dict(self.verses_by_ref[direct_ref])
            exact_verse["score"] = 1.0
            exact_verse["match_type"] = "exact_reference"
            
            # Retrieve companion verses if top_k > 1
            other_results = [
                v for v in self.search(
                    re.sub(r"(?:chapter|ch|bg|verse|sloka|\d+[:.]\d+)", "", query, flags=re.I).strip() or "krishna wisdom",
                    top_k=top_k,
                    api_key=api_key
                )
                if (v.get("chapter"), v.get("verse")) != direct_ref
            ]
            return [exact_verse] + other_results[:top_k - 1]

        # 2. Sparse BM25 scores
        bm25_raw = self._bm25_scores(query)
        max_bm25 = max(bm25_raw) if bm25_raw and max(bm25_raw) > 0 else 1.0
        normalized_bm25 = [s / max_bm25 for s in bm25_raw]

        # 3. Dense semantic vector scores
        dense_scores = [0.0] * len(self.verses)
        dense_available = False

        if api_key and self.embeddings is not None and np is not None:
            query_vec = self._embed_query(query, api_key)
            if query_vec is not None:
                q_arr = np.array(query_vec, dtype=np.float32)
                q_norm = np.linalg.norm(q_arr)
                if q_norm > 0:
                    q_arr = q_arr / q_norm
                    # Cosine similarities (dot product with unit-norm vectors)
                    raw_sims = np.dot(self.embeddings, q_arr)
                    
                    # Map back to doc index
                    for doc_idx, v in enumerate(self.verses):
                        vid = v.get("id")
                        if vid in self.embedding_id_to_idx:
                            emb_idx = self.embedding_id_to_idx[vid]
                            # Scale cosine similarity from [-1, 1] to [0, 1]
                            dense_scores[doc_idx] = float(max(0.0, raw_sims[emb_idx]))
                    dense_available = True

        # 4. Fusion
        fused_results = []
        for idx, v in enumerate(self.verses):
            if dense_available:
                score = (dense_weight * dense_scores[idx]) + (sparse_weight * normalized_bm25[idx])
                match_type = "hybrid"
            else:
                score = normalized_bm25[idx]
                match_type = "bm25_lexical"

            if score > 0.001 or idx < 5: # Keep candidates
                verse_copy = dict(v)
                verse_copy["score"] = round(float(score), 4)
                verse_copy["dense_score"] = round(float(dense_scores[idx]), 4) if dense_available else None
                verse_copy["bm25_score"] = round(float(normalized_bm25[idx]), 4)
                verse_copy["match_type"] = match_type
                fused_results.append(verse_copy)

        # Sort descending by score
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        return fused_results[:top_k]

    # --- Prompt Context Builder ---
    def build_grounding_context(self, retrieved_verses: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved Gita verses into a clean, authoritative context block
        for the LLM system/user prompt.
        """
        if not retrieved_verses:
            return ""

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📖 AUTHENTIC BHAGAVAD GITA SCRIPTURAL RETRIEVAL (RAG CONTEXT)",
            "The following authentic verses have been retrieved as directly relevant to the user's inquiry.",
            "Ground your counsel in these verses and cite their Chapter & Verse accurately in the '📖 Gita Principle' section.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        for idx, v in enumerate(retrieved_verses, 1):
            ref = v.get("reference", f"Chapter {v.get('chapter')}, Verse {v.get('verse')}")
            ch_name = v.get("chapter_name", "")
            slok = v.get("slok", "").replace("\n", " ")
            trans = v.get("transliteration", "").replace("\n", " ")
            en = v.get("translation_en", "")
            comm = v.get("commentary_en", "")

            lines.append(f"\n[Retrieved Shloka {idx}]: {ref} ({ch_name})")
            lines.append(f"• Sanskrit Shloka: {slok}")
            lines.append(f"• Transliteration: {trans}")
            lines.append(f"• Authentic Translation: {en}")
            if comm:
                lines.append(f"• Spiritual Meaning / Commentary: {comm[:250]}...")

        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    # --- Exploration Helpers ---
    def get_verse(self, chapter: int, verse: int) -> Optional[Dict[str, Any]]:
        return self.verses_by_ref.get((chapter, verse))

    def get_chapters(self) -> List[Dict[str, Any]]:
        return self.chapters

# Global Singleton instance
_rag_instance: Optional[GitaRAG] = None

def get_rag() -> GitaRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = GitaRAG()
    return _rag_instance
