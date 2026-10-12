"""
rag.py — 검색과 답변 생성. 화면에 출력하지 않고 값만 돌려준다
         (터미널용 ask.py와 웹 서버 server.py가 함께 쓴다)

    입력 문장(영어만) → 벡터 검색(의미가 비슷한 것) + 키워드 검색(같은 단어가 있는 것)
              → 두 순위를 합쳐 상위 몇 개 발췌문 선택
              → 발췌문 + 입력 문장을 LLM에 전달 → 답변
"""
import re

from config import CANDIDATES, COLLECTION, DB_DIR, EMBED_MODEL, QUERY_PREFIX, TOP_K
from llm import chat

SYSTEM_PROMPT = """You are a DNV class rule review assistant helping ship structural designers.
The user enters, in one English sentence, a change made to a drawing or an issue found in it.
Using only the "DNV rule excerpts" given below, find and explain the rule requirements related to that item.

Rules:
- Use only what is in the excerpts. Do not make up rule content from memory that is not in the excerpts.
- If the excerpts contain nothing relevant, say clearly: "No relevant clause was found in the provided DNV documents."
- Every time you state a requirement, cite its basis with the [excerpt number] and the clause number.
  Example: [1] Pt.3 Ch.6 Sec.4 [2.1.1]
- Formulas and figures are not included in the excerpts (they are images in the PDF). If a requirement
  depends on a formula or figure, do not guess the values; tell the user to check that page of the original.
- Always answer in English. Keep clause numbers and technical terms exactly as in the original text.

Answer format:
1. Summary of the relevant rules (2-3 sentences)
2. Requirements / items to check (itemized, each with its basis)
3. Points to note (if anything cannot be judged from the excerpts alone)"""

# 문서와 임베딩 모델이 영어 전용이므로, 한글이 들어 있는 문장은 받지 않는다
HANGUL_RE = re.compile(r"[ㄱ-ㅎㅏ-ㅣ가-힣]")
ENGLISH_ONLY = "English only. Please enter the sentence in English."


def tokenize(text):
    """키워드 검색용: 소문자로 바꾼 뒤 영문, 숫자 단어 단위로 자른다"""
    return re.findall(r"[a-z0-9]+", text.lower())


def load_index():
    import chromadb
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer

    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        raise SystemExit("The DB does not exist yet. Run python ingest.py first.")

    everything = collection.get(include=["documents", "metadatas"])   # 저장된 chunk 전체
    chunks = {
        chunk_id: {"text": text, "meta": meta}
        for chunk_id, text, meta in zip(everything["ids"], everything["documents"], everything["metadatas"])
    }
    ids = list(chunks)
    bm25 = BM25Okapi([tokenize(chunks[i]["text"]) for i in ids])
    model = SentenceTransformer(EMBED_MODEL)
    return {"collection": collection, "chunks": chunks, "ids": ids, "bm25": bm25, "model": model}


def search(index, query):
    """query와 관련 있는 chunk를 TOP_K개 찾아 돌려준다 (벡터 검색 + 키워드 검색)"""
    # (1) 벡터 검색: 질문을 벡터로 바꿔서 가까운 chunk 찾기
    query_vector = index["model"].encode(QUERY_PREFIX + query, normalize_embeddings=True)
    result = index["collection"].query(query_embeddings=[query_vector.tolist()], n_results=CANDIDATES)
    vector_ranking = result["ids"][0]

    # (2) 키워드 검색(BM25): 질문의 단어가 많이, 드물게 나오는 chunk일수록 높은 점수
    scores = index["bm25"].get_scores(tokenize(query))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:CANDIDATES]
    keyword_ranking = [index["ids"][i] for i in order]

    # (3) 순위 합치기(RRF): 두 검색에서 모두 상위권인 chunk가 최종 상위로 올라온다
    combined = {}
    for ranking in (vector_ranking, keyword_ranking):
        for rank, chunk_id in enumerate(ranking):
            combined[chunk_id] = combined.get(chunk_id, 0) + 1 / (60 + rank)
    best = sorted(combined, key=combined.get, reverse=True)[:TOP_K]
    return [index["chunks"][chunk_id] for chunk_id in best]


def excerpts(found):
    """찾은 chunk들에 번호를 붙여 한 덩어리 글로 만든다 (LLM에 보내거나 그대로 보여 주는 용도)"""
    text = ""
    for number, chunk in enumerate(found, start=1):
        meta = chunk["meta"]
        text += f"\n[{number}] (Edition {meta['edition']}, p.{meta['page']})\n{chunk['text']}\n"
    return text


def generate(question, found):
    """입력 문장 + 번호를 붙인 발췌문을 LLM에 보내고 답변 글을 돌려받는다"""
    user_message = f"[Input sentence]\n{question}\n\n[DNV rule excerpts]{excerpts(found)}"
    return chat(SYSTEM_PROMPT, user_message)
