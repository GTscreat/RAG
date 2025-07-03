import json
import os

NER_RESULTS_PATH = "data/ner_results.json"
NER_RATING_PATH = "data/tamplates/ner_rating.json"

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    ner_results = load_json(NER_RESULTS_PATH)
    ner_rating = load_json(NER_RATING_PATH)

    # Ստեղծել արդեն առկա word-ների հավաքածու
    existing_words = set(item["word"] for item in ner_rating if "word" in item)

    # Ավելացնել նոր word-եր, եթե չկան
    for article in ner_results:
        for ent in article.get("entities", []):
            word = ent.get("word", "")
           
            if word and word not in existing_words:
                ner_rating.append({"word": word, "score": ""})
                existing_words.add(word)

    save_json(ner_rating, NER_RATING_PATH)

if __name__ == "__main__":
    main()