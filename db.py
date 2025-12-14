# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, LargeBinary, ForeignKey, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import JSONB  # Ներմուծում ենք JSONB-ն PostgreSQL-ի համար
from sqlalchemy.orm import sessionmaker, declarative_base

# --- 1. Միացման կարգավորումները փոխում ենք PostgreSQL-ի ---
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD") # <-- Փոխարինեք ձեր գաղտնաբառով
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# SQLAlchemy-ի միացման հասցեն PostgreSQL-ի համար
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey('websites.id')) # Ավելացնում ենք ForeignKey
    url = Column(String)
    title = Column(String)
    content = Column(Text)
    published_at = Column(DateTime)
    meta = Column(JSON, nullable=True)


class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news.id', ondelete='CASCADE'), nullable=False) # nullable=False-ը ցանկալի է
    chunk_content = Column(Text, nullable=True)
    chunk_start = Column(Integer, nullable=True)
    chunk_end = Column(Integer, nullable=True)
    embedding = Column(LargeBinary, nullable=True)

class Parameter(Base):
    __tablename__ = "parameters"
    id = Column(Integer, ForeignKey('news.id', ondelete='CASCADE'), primary_key=True)
    category = Column(String, nullable=True)
    aver_embedding = Column(LargeBinary, nullable=True)
    similarity = Column(JSONB, nullable=True)
    entities = Column(JSONB, nullable=True) # <<< ԱՎԵԼԱՑՎԱԾ ՆՈՐ ՍՅՈՒՆԱԿ

class Rank(Base):
    __tablename__ = "ranks"
    # One-to-One կապ
    id = Column(Integer, ForeignKey('news.id', ondelete='CASCADE'), primary_key=True)
    topic_importance = Column(Float, nullable=True)
    ner_content_importance = Column(Float, nullable=True)
    frequency_importance = Column(Float, nullable=True)
    source_importance = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)


class Top(Base):
    __tablename__ = "top"
    # One-to-One կապ
    id = Column(Integer, ForeignKey('news.id', ondelete='CASCADE'), primary_key=True)
    total_score = Column(Float, nullable=True)
    ai_score = Column(Float, nullable=True)
    urgency = Column(Integer, nullable=True)
    sentiment = Column(String, nullable=True)
    geopolitical = Column(String, nullable=True)
    final_score = Column(Float, nullable=True)


class Processed(Base):
    __tablename__ = "processed"
    # One-to-One կապ, base_id-ն է առաջնային բանալին
    base_id = Column(Integer, ForeignKey('news.id', ondelete='CASCADE'), primary_key=True)
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

# class Website(Base):
#     __tablename__ = 'websites'
#     id = Column(Integer, primary_key=True)
#     url = Column(String, unique=True) 

Base.metadata.create_all(engine)