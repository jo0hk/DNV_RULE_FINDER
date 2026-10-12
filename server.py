"""
server.py — 웹 화면(web/ 폴더)과 API를 함께 띄우는 서버

    GET  /api/health       chunk 개수, 사용 중인 LLM
    POST /api/search       입력 문장 → 관련 발췌문 (LLM 호출 없음, 바로 응답)
    POST /api/answer       입력 문장 → 발췌문 + LLM 답변
    GET  /api/pdf/{파일}   규정 원문 PDF (출처 카드의 "Open PDF" 링크용)

실행:  uvicorn server:app --port 8000      → 브라우저에서 http://127.0.0.1:8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import rag
from config import BASE_DIR, DOCS_DIR
from llm import MODEL, PROVIDER

state = {}


@asynccontextmanager
async def lifespan(app):
    """서버가 뜰 때 DB와 임베딩 모델을 한 번만 불러온다"""
    index = rag.load_index()
    state["index"] = index
    state["files"] = {chunk["meta"]["file"] for chunk in index["chunks"].values()}
    yield


app = FastAPI(title="DNV Rule Finder", lifespan=lifespan)


class Question(BaseModel):
    question: str = Field(max_length=2000)


def to_source(number, chunk):
    """chunk 하나를 화면에 보낼 모양으로 바꾼다"""
    meta = chunk["meta"]
    body = chunk["text"].partition("\n")[2]     # 첫 줄("ref | path")은 따로 보내므로 뗀다
    return {
        "number": number, "ref": meta["ref"], "path": meta["path"], "edition": meta["edition"],
        "page": meta["page"], "pdf_page": meta["pdf_page"], "file": meta["file"], "text": body,
    }


def find(question):
    """입력 문장을 검사한 뒤 검색한다. 반환값: (다듬은 문장, 찾은 chunk 목록)"""
    question = question.strip()
    if not question:
        raise HTTPException(400, "Please enter a sentence.")
    if rag.HANGUL_RE.search(question):
        raise HTTPException(400, rag.ENGLISH_ONLY)
    return question, rag.search(state["index"], question)


@app.get("/api/health")
def health():
    return {
        "chunks": len(state["index"]["ids"]),
        "llm": f"{PROVIDER} / {MODEL}" if PROVIDER else None,
    }


@app.post("/api/search")
def search(body: Question):
    _, found = find(body.question)
    return {"sources": [to_source(n, chunk) for n, chunk in enumerate(found, start=1)]}


@app.post("/api/answer")
def answer(body: Question):
    if not PROVIDER:
        raise HTTPException(503, "No LLM API key is configured in .env.")
    question, found = find(body.question)
    try:
        text = rag.generate(question, found)
    except (Exception, SystemExit) as error:    # 키 오류, 네트워크 오류, 알 수 없는 LLM_PROVIDER 등
        raise HTTPException(502, f"The LLM request failed: {error}")
    return {
        "answer": text,
        "sources": [to_source(n, chunk) for n, chunk in enumerate(found, start=1)],
    }


@app.get("/api/pdf/{name}")
def pdf(name: str):
    # DB에 들어 있는 PDF 파일 이름만 허용한다 (다른 경로의 파일을 읽지 못하게)
    path = DOCS_DIR / name
    if name not in state["files"] or not path.is_file():
        raise HTTPException(404, "PDF not found.")
    return FileResponse(path, media_type="application/pdf")


# API 경로가 아닌 나머지 주소는 web/ 폴더의 파일을 그대로 보여 준다
app.mount("/", StaticFiles(directory=BASE_DIR / "web", html=True), name="web")
