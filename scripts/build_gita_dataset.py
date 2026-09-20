"""
Builds the unified canonical Bhagavad Gita dataset for Gita AI Guide.
Downloads verses, chapters, translations, and commentaries from open-source canonical sources (gita/gita)
and generates a structured, verified dataset: data/gita_verses.json and data/chapters.json.
"""

import os
import json
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/gita/gita/main/data"

def fetch_json(endpoint: str):
    url = f"{BASE_URL}/{endpoint}"
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Gita-AI-Guide/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    target_repo = r"C:\Users\vijit juneja\.gemini\antigravity\scratch\gita-ai-guide"
    data_dir = os.path.join(target_repo, "data")
    scripts_dir = os.path.join(target_repo, "scripts")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)

    print("--- 1. Fetching Raw Data ---")
    verses_raw = fetch_json("verse.json")
    translations_raw = fetch_json("translation.json")
    chapters_raw = fetch_json("chapters.json")
    commentaries_raw = fetch_json("commentary.json")

    print(f"Loaded: {len(verses_raw)} verses, {len(translations_raw)} translations, {len(chapters_raw)} chapters, {len(commentaries_raw)} commentaries")

    # Map chapters by chapter_number
    chapters_map = {}
    for ch in chapters_raw:
        c_num = ch.get("chapter_number")
        chapters_map[c_num] = {
            "chapter_number": c_num,
            "name": ch.get("name", "").strip(),
            "name_transliterated": ch.get("name_transliterated", "").strip(),
            "name_translation": ch.get("name_translation", "").strip(),
            "name_meaning": ch.get("name_meaning", "").strip(),
            "summary": ch.get("chapter_summary", "").strip(),
            "summary_hi": ch.get("chapter_summary_hindi", "").strip(),
            "verses_count": ch.get("verses_count", 0)
        }

    # Save clean chapters.json
    chapters_path = os.path.join(data_dir, "chapters.json")
    with open(chapters_path, "w", encoding="utf-8") as f:
        json.dump(list(chapters_map.values()), f, ensure_ascii=False, indent=2)
    print(f"Saved {len(chapters_map)} chapters to {chapters_path}")

    # Map translations by verse_id
    translations_map = {}
    for t in translations_raw:
        vid = t.get("verse_id")
        if vid not in translations_map:
            translations_map[vid] = []
        translations_map[vid].append(t)

    # Map commentaries by verse_id
    commentaries_map = {}
    for c in commentaries_raw:
        vid = c.get("verse_id")
        if vid not in commentaries_map:
            commentaries_map[vid] = []
        commentaries_map[vid].append(c)

    # Compile structured verses
    compiled_verses = []
    for v in sorted(verses_raw, key=lambda x: (x.get("chapter_number", 0), x.get("verse_number", 0))):
        vid = v.get("id")
        c_num = v.get("chapter_number")
        v_num = v.get("verse_number")
        ch_info = chapters_map.get(c_num, {})

        # Find best translations
        v_trans = translations_map.get(vid, [])
        en_sivananda = ""
        en_purohit = ""
        en_gambir = ""
        hi_ramsukhdas = ""

        for t in v_trans:
            author = (t.get("authorName") or "").strip()
            lang = (t.get("lang") or "").strip().lower()
            desc = (t.get("description") or "").strip()
            
            if lang == "english":
                if "Sivananda" in author:
                    en_sivananda = desc
                elif "Purohit" in author:
                    en_purohit = desc
                elif "Gambirananda" in author:
                    en_gambir = desc
            elif lang == "hindi":
                if "Ramsukhdas" in author:
                    hi_ramsukhdas = desc

        # Prefer Sivananda -> Purohit -> Gambirananda for primary English
        primary_en = en_sivananda or en_purohit or en_gambir
        if not primary_en and v_trans:
            for t in v_trans:
                if t.get("lang") == "english" and t.get("description"):
                    primary_en = t["description"].strip()
                    break

        # Find commentaries
        v_comms = commentaries_map.get(vid, [])
        comm_sivananda = ""
        for c in v_comms:
            author = (c.get("authorName") or "").strip()
            lang = (c.get("lang") or "").strip().lower()
            if "Sivananda" in author and lang == "english":
                comm_sivananda = (c.get("description") or "").strip()
                break

        # Build clean verse record
        verse_obj = {
            "id": vid,
            "chapter": c_num,
            "verse": v_num,
            "reference": f"Chapter {c_num}, Verse {v_num}",
            "short_ref": f"BG {c_num}.{v_num}",
            "chapter_name": ch_info.get("name_transliterated", ""),
            "chapter_meaning": ch_info.get("name_meaning", ""),
            "slok": (v.get("text") or "").strip(),
            "transliteration": (v.get("transliteration") or "").strip(),
            "word_meanings": (v.get("word_meanings") or "").strip(),
            "translation_en": primary_en,
            "translation_hi": hi_ramsukhdas,
            "commentary_en": comm_sivananda[:1200] if comm_sivananda else ""
        }
        compiled_verses.append(verse_obj)

    verses_path = os.path.join(data_dir, "gita_verses.json")
    with open(verses_path, "w", encoding="utf-8") as f:
        json.dump(compiled_verses, f, ensure_ascii=False, indent=2)

    print(f"Successfully compiled and saved {len(compiled_verses)} verses to {verses_path}!")

if __name__ == "__main__":
    main()
