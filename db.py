# db.py
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, JSON, PickleType
)
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. Լրատվական նյութերի հիմնական աղյուսակ (content.json)
class Content(Base):
    __tablename__ = "content"
    id = Column(Integer, primary_key=True, index=True)
    website = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    url = Column(String)
    meta = Column(JSON, nullable=True)   # image, iframe
    # Եթե ապագայում պետք լինի՝ DateTime, բայց հիմա թողնում ենք str ձևաչափով.
    published_at = Column(String, index=True)

# 2. Embeddings աղյուսակ (embeddings.json)
class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)  # Չանկի id (autoincrement)
    article_id = Column(Integer, index=True)
    website = Column(String, nullable=True)
    title = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    url = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    chunk_content = Column(Text, nullable=True)
    chunk_start = Column(Integer, nullable=True)
    chunk_end = Column(Integer, nullable=True)
    # Embedding-ը pickle-ով. PostgreSQL-ում հետագայում՝ ARRAY կամ JSONB:
    embedding = Column(PickleType, nullable=True)

# 3. NER արդյունքներ (ner_results.json)
class NERResult(Base):
    __tablename__ = "ner_results"
    id = Column(Integer, primary_key=True, index=True)
    # entities-ը JSON դաշտում (entities = [{"entity_group":, ...}, ...])
    entities = Column(JSON, nullable=True)

# 4. Parameters աղյուսակ (parameters.json)
class Parameter(Base):
    __tablename__ = "parameters"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=True)
    aver_embedding = Column(PickleType, nullable=True)
    similarity = Column(JSON, nullable=True)  # [{"id": ..., "similarity_index": ...}, ...]

# 5. NER rating աղյուսակ (ner_rating.json)
class NERRating(Base):
    __tablename__ = "ner_rating"
    word = Column(String, primary_key=True, index=True, unique=True)
    score = Column(Float, nullable=True)

# 6. Rank աղյուսակ (ranks.json)
class Rank(Base):
    __tablename__ = "ranks"
    id = Column(Integer, primary_key=True, index=True)
    topic_importance = Column(Float, nullable=True)
    ner_content_importance = Column(Float, nullable=True)
    frequency_importance = Column(Float, nullable=True)
    source_importance = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)
