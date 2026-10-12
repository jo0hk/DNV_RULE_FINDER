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

# ---- 아래는 서버를 인터넷에 공개할 때만 쓰는 설정 (로컬에서는 비워 두면 된다) ----
# 화면을 서버와 다른 주소(GitHub Pages)에 올렸을 때, 그 주소에서 오는 요청을 허용한다. 쉼표로 여러 개
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
# LLM 답변 하루 상한 (API 요금 보호). 0이면 제한 없음
ANSWER_LIMIT_PER_DAY = int(os.getenv("ANSWER_LIMIT_PER_DAY") or 0)
# Cloud Run 위에서 돌고 있는지 (Cloud Run이 K_SERVICE를 넣어 준다)
DEPLOYED = bool(os.getenv("K_SERVICE"))
