import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, PickleType
from sqlalchemy.orm import declarative_base, sessionmaker
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ---- Տվյալներ ----
INPUT_JSON = "data/ner_indexed_fixed.json"        # JSON path
DB_PATH = "data/nerdatabase+.db"              # SQLite db path
MODEL_PATH = os.getenv(
    "ARMENIAN_EMBEDDING_MODEL_PATH",
    "Metric-AI/armenian-text-embeddings-1"
)

Base = declarative_base()

class NERGroup(Base):
    __tablename__ = "ner_entities"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_group = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    index_code = Column(Integer, nullable=False)
    embedding = Column(PickleType, nullable=True)

# ---- Մոդել բեռնում ----
model = SentenceTransformer(MODEL_PATH)

def make_entity_group(row):
    # levels as string, skipping None or empty
    levels = [row.get('level1'), row.get('level2'), row.get('level3')]
    return " ".join([l for l in levels if l and str(l).strip() != ""])

def main():
    # 1. Load JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        entities = json.load(f)
    
    # 2. Պատրաստել տվյալներ էմբեդդինգի համար
    rows = []
    for row in entities:
        entity_group = make_entity_group(row)
        index_code = int(row['index_code'])
        rows.append({
            "entity_group": entity_group,
            "index_code": index_code
        })

    # 3. Էմբեդդինգների հաշվարկ
    texts = [r["entity_group"] for r in rows]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    # 4. ՏԲ կառուցում և լցնում
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for row, emb in tqdm(zip(rows, embeddings), total=len(rows)):
        db_row = NERGroup(
            entity_group=row["entity_group"],
            score=1.0,
            index_code=row["index_code"],
            embedding=emb
        )
        session.add(db_row)
    session.commit()
    session.close()
    print(f"Embedding DB saved: {DB_PATH}")

if __name__ == "__main__":
    main()
