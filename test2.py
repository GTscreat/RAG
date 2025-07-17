import re
import json
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
import torch
from tqdm import tqdm  # Պրոգրեսի սանդղակի համար

# Նոր տվյալների բազայի ինտեգրում
NER_DATABASE_URL = "sqlite:///./data/nerdatabase.db"
engine = create_engine(NER_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Նոր աղյուսակի սահմանում
class NEREntity(Base):
    __tablename__ = "ner_entities"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_group = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    word = Column(String, nullable=False)

# Տվյալների բազայի ստեղծում
Base.metadata.create_all(bind=engine)

def load_ner_pipeline():
    """
    Բեռնում է NER մոդելը և tokenizer-ը։
    """
    model_name = "daviddallakyan2005/armenian-ner"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"  # Օգտագործել GPU, եթե հասանելի է
    model = model.to(device)  # Մոդելը տեղափոխել GPU կամ CPU
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple", device=0 if torch.cuda.is_available() else -1)
    return ner_pipeline

def merge_entities(entities, group_key="entity_group", word_key="word", start_key="start", end_key="end", score_key="score"):
    """
    Միավորում է NER արդյունքները՝ նույն խմբի և հարակից բառերը միավորելով։
    """
    if not entities:
        return []
    merged = []
    entities = sorted(entities, key=lambda x: x[start_key])
    buffer = entities[0].copy()
    for ent in entities[1:]:
        if ent[group_key] == buffer[group_key] and ent[start_key] == buffer[end_key]:
            buffer[word_key] += ent[word_key]
            buffer[end_key] = ent[end_key]
            buffer[score_key] = max(buffer[score_key], ent[score_key])
        else:
            merged.append(buffer)
            buffer = ent.copy()
    merged.append(buffer)
    return merged

def process_and_save_article(article, ner_pipeline, session, existing_words):
    """
    Մշակում է մեկ հոդված և պահպանում է դրա NER արդյունքները տվյալների բազայում։
    """
    text = article  # Քանի որ article-ը տող է, այն ուղղակի օգտագործվում է որպես տեքստ
    ner_results = ner_pipeline(text)
    merged_entities = merge_entities(ner_results)
    new_entities_count = 0

    for entity in merged_entities:
        if entity["word"] not in existing_words:  # Ստուգել, արդյոք word-ն արդեն կա
            ner_entity = NEREntity(
                entity_group=entity["entity_group"],
                score=entity["score"],
                word=entity["word"]
            )
            session.add(ner_entity)
            existing_words.add(entity["word"])  # Ավելացնել նոր word-ը հավաքածուին
            new_entities_count += 1

    return new_entities_count

if __name__ == "__main__":
    # Կարդալ JSON ֆայլը
    with open("data/content_only.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"Կարդացվեց {len(articles)} հոդված")

    # Ներբեռնել NER pipeline-ը
    ner_pipeline = load_ner_pipeline()

    # Սկսել սեսիան
    session = SessionLocal()
    existing_words = {row.word for row in session.query(NEREntity.word).all()}  # Գոյություն ունեցող բառերի հավաքածու

    for article in tqdm(articles, desc="Մշակվում են հոդվածները"):
        process_and_save_article(article, ner_pipeline, session, existing_words)

    session.commit()
    session.close()
    print(f"NER արդյունքները հաջողությամբ պահպանվեցին տվյալների բազայում։")