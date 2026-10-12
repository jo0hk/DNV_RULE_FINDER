"""
config.py — ingest.py와 ask.py가 함께 쓰는 설정값 모음
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DOCS_DIR = Path(os.getenv("DOCS_DIR") or BASE_DIR.parent / "DNV")
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION = "dnv_rules"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

TOP_K = 6          # LLM에게 넘겨줄 발췌문 개수
CANDIDATES = 30    # 벡터 검색 / 키워드 검색에서 각각 뽑는 후보 개수
