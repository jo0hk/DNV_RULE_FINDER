"""
train/make_dataset.py — 검색 모델 학습 데이터 만들기

    chunk마다 LLM에게 "이 조항이 답이 되는 설계자 질문"을 3개씩 쓰게 해서
    (질문, 정답 chunk) 쌍을 train/data/queries.jsonl 에 쌓는다.

    평가용 질문(eval/questions.jsonl)의 정답 chunk는 학습에서 뺀다.
    그래야 학습한 모델이 처음 보는 조항에서도 잘 찾는지를 정직하게 잴 수 있다.

    중간에 멈춰도 다시 실행하면 이미 만든 chunk는 건너뛴다.

실행:  python train/make_dataset.py              (전체)
       python train/make_dataset.py --limit 16   (앞의 16개만, 시험용)
"""
import argparse
import importlib.util
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import COLLECTION, DB_DIR  # noqa: E402
from llm import MODEL, PROVIDER, chat  # noqa: E402

OUT = ROOT / "train" / "data" / "queries.jsonl"
BATCH = 8          # 한 번에 LLM에 보내는 chunk 수
WORKERS = 4        # 동시에 보내는 요청 수
RETRIES = 10       # 실패한 묶음은 기록하지 않으므로, 다시 실행하면 그 묶음부터 이어서 만든다

PROMPT = """You create training data for a search engine over the DNV rules for classification of ships.
Its users are ship structural designers who type ONE short English sentence: a change made on a drawing,
a design issue they found, or a question.

For each rule excerpt below, write 3 different queries that the excerpt answers:
1. a drawing change or design note, with concrete values if the excerpt gives any
2. a question as a designer would ask it
3. a short informal comment in everyday shipyard wording

Rules:
- Do not copy distinctive phrases from the excerpt. Use synonyms and shipyard jargon.
- Do not mention rule, section or clause numbers.
- Each query under 25 words.
- If an excerpt contains no real requirement (e.g. only a list of symbols), give it an empty list.

Answer with JSON only, no explanation: {"<excerpt id>": ["query 1", "query 2", "query 3"], ...}"""


def load_eval_gold(metas, docs):
    """평가 질문들의 정답 chunk 번호 (학습에서 뺄 것)"""
    spec = importlib.util.spec_from_file_location("evaluate", ROOT / "eval" / "evaluate.py")
    evaluate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluate)
    questions = [json.loads(line) for line in (ROOT / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    gold = set()
    for q in questions:
        gold |= evaluate.gold_positions(q, metas, docs)
    return gold


def parse(text):
    """LLM 답에서 JSON 부분만 꺼낸다 (```json ... ``` 으로 감싸 오는 경우가 있다)"""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("JSON not found")
    return json.loads(match.group(0))


def ask(batch):
    """chunk 묶음 하나에 대한 질문을 받아 온다. 실패하면 조금 쉬었다가 다시 시도"""
    message = "\n\n".join(f"[{cid}]\n{doc}" for cid, doc in batch)
    for attempt in range(RETRIES):
        try:
            result = parse(chat(PROMPT, message))
            return {cid: [q.strip() for q in result.get(cid, []) if isinstance(q, str) and q.strip()][:3] for cid, _ in batch}
        except (Exception, SystemExit) as error:
            wait = min(5 * 2 ** attempt, 300)   # 서버가 붐비면(503) 최대 5분까지 기다렸다가 다시
            print(f"  다시 시도 ({attempt + 1}/{RETRIES}, {wait}초 뒤): {type(error).__name__}: {str(error)[:120]}", flush=True)
            time.sleep(wait)
    print(f"  실패해서 건너뜀: {[cid for cid, _ in batch]}", flush=True)
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="앞에서부터 이 개수의 chunk만 (시험용)")
    args = parser.parse_args()
    if not PROVIDER:
        raise SystemExit(".env에 LLM API 키가 없습니다.")

    import chromadb
    data = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION).get(include=["documents", "metadatas"])
    ids, docs, metas = data["ids"], data["documents"], data["metadatas"]
    held_out = load_eval_gold(metas, docs)

    done = set()
    if OUT.exists():
        done = {json.loads(line)["chunk_id"] for line in OUT.read_text(encoding="utf-8").splitlines() if line.strip()}
    todo = [(ids[i], docs[i]) for i in range(len(ids)) if i not in held_out and ids[i] not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f"LLM: {PROVIDER} / {MODEL} | 전체 chunk {len(ids)}개, 평가용으로 뺀 chunk {len(held_out)}개, "
          f"이미 만든 chunk {len(done)}개, 이번에 만들 chunk {len(todo)}개")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    made = 0
    with open(OUT, "a", encoding="utf-8") as out, ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(ask, batch) for batch in batches]
        for n, future in enumerate(as_completed(futures), start=1):
            for cid, queries in future.result().items():
                out.write(json.dumps({"chunk_id": cid, "queries": queries}, ensure_ascii=False) + "\n")
                made += len(queries)
            out.flush()
            if n % 20 == 0 or n == len(batches):
                print(f"  {n}/{len(batches)} 묶음 완료, 질문 {made}개", flush=True)
    print(f"저장: {OUT}")


if __name__ == "__main__":
    main()
