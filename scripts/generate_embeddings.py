"""
Generates precomputed dense embeddings for all 701 verses of the Bhagavad Gita using Google's gemini-embedding-001 model.
Features:
- Checkpointing: Saves progress after every batch to resume effortlessly
- Rate Limit Handling: Detects HTTP 429 and waits with exponential backoff
- Compact Batching: Uses batch size of 20 to comfortably stay within rate & token limits
"""

import os
import time
import json
import urllib.request
import urllib.error
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def embed_batch(texts, api_key, model="models/gemini-embedding-001"):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:batchEmbedContents?key={api_key}"
    payload = {
        "requests": [
            {
                "model": model,
                "content": {"parts": [{"text": t}]}
            }
            for t in texts
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        embeddings = [e["values"] for e in res.get("embeddings", [])]
        return embeddings

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(repo_root, "data")
    verses_path = os.path.join(data_dir, "gita_verses.json")
    checkpoint_path = os.path.join(data_dir, "embeddings_checkpoint.json")
    out_path = os.path.join(data_dir, "gita_embeddings.npz")

    if not os.path.exists(verses_path):
        raise FileNotFoundError(f"Missing {verses_path}. Please run build_gita_dataset.py first.")

    with open(verses_path, "r", encoding="utf-8") as f:
        verses = json.load(f)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required to generate embeddings.")

    # Load existing checkpoint if available
    saved_embeddings = {}
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                saved_embeddings = json.load(f)
            print(f"Loaded existing checkpoint with {len(saved_embeddings)} embedded verses.")
        except Exception as e:
            print(f"Failed to load checkpoint: {e}. Starting fresh.")
            saved_embeddings = {}

    texts_to_embed = []
    verse_ids = []
    for v in verses:
        verse_ids.append(v["id"])
        # Formulate rich concise semantic text
        content = (
            f"Bhagavad Gita {v['reference']} ({v['chapter_name']}).\n"
            f"Transliteration: {v['transliteration']}\n"
            f"Translation: {v['translation_en']}\n"
        )
        if v.get("word_meanings"):
            content += f"Word meanings: {v['word_meanings'][:150]}\n"
        texts_to_embed.append(content.strip())

    batch_size = 20

    for i in range(0, len(texts_to_embed), batch_size):
        batch_slice = slice(i, min(i + batch_size, len(texts_to_embed)))
        batch_ids = verse_ids[batch_slice]
        
        # Check if all items in this batch are already completed
        if all(str(vid) in saved_embeddings for vid in batch_ids):
            continue

        batch_texts = texts_to_embed[batch_slice]
        print(f"Embedding verses {i+1} to {i + len(batch_texts)} of {len(texts_to_embed)}...")

        success = False
        wait_time = 5
        while not success:
            try:
                embeddings = embed_batch(batch_texts, api_key)
                if len(embeddings) != len(batch_texts):
                    raise ValueError(f"Batch returned {len(embeddings)} vectors, expected {len(batch_texts)}")
                
                # Update saved dict
                for vid, emb in zip(batch_ids, embeddings):
                    saved_embeddings[str(vid)] = emb

                # Save checkpoint
                with open(checkpoint_path, "w", encoding="utf-8") as f:
                    json.dump(saved_embeddings, f)

                success = True
                print(f"  ✓ Saved checkpoint ({len(saved_embeddings)}/{len(texts_to_embed)} total)")
                time.sleep(3) # Respectful delay between batches

            except urllib.error.HTTPError as he:
                if he.code == 429:
                    print(f"  Rate limited (429). Cooling down for {wait_time}s...")
                    time.sleep(wait_time)
                    wait_time = min(wait_time * 2, 45) # Exponential backoff up to 45s
                else:
                    print(f"  HTTP error {he.code}: {he.read().decode()}. Waiting 10s...")
                    time.sleep(10)
            except Exception as e:
                print(f"  Error: {e}. Waiting 10s...")
                time.sleep(10)

    # Reassemble matrix in original order
    ordered_matrix = []
    for vid in verse_ids:
        ordered_matrix.append(saved_embeddings[str(vid)])

    matrix = np.array(ordered_matrix, dtype=np.float32)
    print(f"Finished embedding all {len(ordered_matrix)} verses! Matrix shape: {matrix.shape}")

    # L2 normalize
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_matrix = matrix / norms

    # Save to final compressed file
    np.savez_compressed(
        out_path,
        embeddings=normalized_matrix,
        ids=np.array(verse_ids, dtype=np.int32)
    )

    # Clean up checkpoint file
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    file_size = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Successfully created final index at {out_path} ({file_size:.2f} MB)!")

if __name__ == "__main__":
    main()
