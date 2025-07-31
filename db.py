# db.py
import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, LargeBinary, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB  # Ներմուծում ենք JSONB-ն PostgreSQL-ի համար
from sqlalchemy.orm import sessionmaker, declarative_base

# --- 1. Միացման կարգավորումները փոխում ենք PostgreSQL-ի ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Aylabanutyun1991") # <-- Փոխարինեք ձեր գաղտնաբառով
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "Dpir_database")

# SQLAlchemy-ի միացման հասցեն PostgreSQL-ի համար
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Content(Base):
    __tablename__ = "content"
    id = Column(Integer, primary_key=True) # SERIAL-ը SQLAlchemy-ն ավտոմատ կհասկանա
    website = Column(String)
    title = Column(String)
    content = Column(Text)
    url = Column(String)
    meta = Column(JSONB, nullable=True) # JSON -> JSONB
    published_at = Column(String)


class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE')) # Ավելացվել է կապ
    website = Column(String, nullable=True)
    title = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    url = Column(String, nullable=True)
    meta = Column(JSONB, nullable=True) # JSON -> JSONB
    chunk_content = Column(Text, nullable=True)
    chunk_start = Column(Integer, nullable=True)
    chunk_end = Column(Integer, nullable=True)
    embedding = Column(LargeBinary, nullable=True) # PickleType -> LargeBinary (BYTEA-ի համար)


class NERResult(Base):
    __tablename__ = "ner_results"
    # One-to-One կապ, id-ն և՛ առաջնային, և՛ արտաքին բանալի է
    id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    entities = Column(JSONB, nullable=True) # JSON -> JSONB


class Parameter(Base):
    __tablename__ = "parameters"
    # One-to-One կապ
    id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    category = Column(String, nullable=True)
    aver_embedding = Column(LargeBinary, nullable=True) # PickleType -> LargeBinary
    similarity = Column(JSONB, nullable=True) # JSON -> JSONB

class Rank(Base):
    __tablename__ = "ranks"
    # One-to-One կապ
    id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    topic_importance = Column(Float, nullable=True)
    ner_content_importance = Column(Float, nullable=True)
    frequency_importance = Column(Float, nullable=True)
    source_importance = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)


class Top(Base):
    __tablename__ = "top"
    # One-to-One կապ
    id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    total_score = Column(Float, nullable=True)
    ai_score = Column(Float, nullable=True)
    urgency = Column(Integer, nullable=True)
    sentiment = Column(String, nullable=True)
    geopolitical = Column(String, nullable=True)
    final_score = Column(Float, nullable=True)


class Processed(Base):
    __tablename__ = "processed"
    # One-to-One կապ, base_id-ն է առաջնային բանալին
    base_id = Column(Integer, ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    title = Column(String, nullable=True)
    generated_content = Column(Text, nullable=True)
    published = Column(String, default=None)
    title_r = Column(String, nullable=True)
    generated_content_r = Column(Text, nullable=True)
    published_r = Column(String, default=None)

class EntityCategory(Base):
    __tablename__ = 'entity_categories'
    id = Column(Integer, primary_key=True)
    code = Column(Integer)
    path = Column(String)
    ner_category_index = Column(Integer)
    ner_category_opp_index = Column(Integer)


class Entity(Base):
    __tablename__ = 'entities'
    id = Column(Integer, primary_key=True)
    entity_group = Column(String)
    score = Column(Float)
    word = Column(String)
    ner_score = Column(Float)
    category_id = Column(Integer, ForeignKey('entity_categories.id', ondelete='SET NULL'), nullable=True)