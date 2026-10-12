"""
ask.py — 영어 문장을 입력하면 DNV 규정에서 관련 조항을 찾아 영어로 답해 주는 터미널용 스크립트
         (검색과 답변 생성은 rag.py에 있고, 여기서는 입력을 받고 결과를 출력만 한다)

    한글이 들어 있는 문장은 받지 않는다 (검색도 LLM 호출도 하지 않음)

실행:  python ask.py                  (문장을 계속 입력하는 대화형)
       python ask.py "sentence"       (한 번만 묻기)
"""
import sys

import rag
from llm import MODEL, PROVIDER

sys.stdout.reconfigure(errors="replace")


def source_line(number, chunk):
    meta = chunk["meta"]
    return (f"[{number}] {meta['ref']} — {meta['path']}\n"
            f"     Edition {meta['edition']}, document p.{meta['page']} "
            f"(file: {meta['file']}, PDF page {meta['pdf_page']})")


def answer(index, question):
    """입력 문장 하나를 처리해서 답변과 출처를 화면에 출력"""
    if rag.HANGUL_RE.search(question):
        print("\n" + rag.ENGLISH_ONLY)
        return

    # 검색
    found = rag.search(index, question)

    # 답변 출력
    if PROVIDER:
        print("\n" + "=" * 30 + " Answer " + "=" * 30)
        print(rag.generate(question, found))
    else:
        print("\n(No API key in .env, so only the retrieved excerpts are shown)")
        print(rag.excerpts(found))

    print("\n" + "=" * 30 + " Sources " + "=" * 30)
    for number, chunk in enumerate(found, start=1):
        print(source_line(number, chunk))


def main():
    print("Loading the DB and model...")
    index = rag.load_index()
    llm_info = f"{PROVIDER} / {MODEL}" if PROVIDER else "none (search results only)"
    print(f"Ready: {len(index['ids'])} chunks, LLM: {llm_info}")

    if len(sys.argv) > 1:
        answer(index, " ".join(sys.argv[1:]))
        return

    while True:
        question = input("\nEnter a sentence in English (press Enter to quit) > ").strip()
        if not question:
            break
        answer(index, question)


if __name__ == "__main__":
    main()
