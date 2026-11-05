"""
eval/synthetic_check.py — 학습이 효과가 있었는지 보조 확인

    평가 질문(eval/questions.jsonl)의 정답 chunk 77개는 학습에서 뺐다.
    이 chunk들에 대해 학습 데이터와 같은 방식(LLM 생성)으로 질문을 만들고,
    기존 모델과 학습 모델이 각 질문의 원래 chunk를 몇 등으로 찾는지 비교한다.

    - 여기서 좋아지고 본 평가에서 그대로면: 모델은 배웠지만, LLM이 만든 질문과
      사람이 쓴 평가 질문의 말투가 달라서 효과가 옮겨지지 않은 것이다.
    - 여기서도 그대로면: 학습 설정(에폭, 층 고정 등) 자체를 바꿔야 한다.

실행:  python eval/synthetic_check.py --model models/bge-small-dnv
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
sys.path.insert(0, str(ROOT))
from config import EMBED_MODEL, QUERY_PREFIX  # noqa: E402
from rag import tokenize  # noqa: E402

QUERIES = EVAL_DIR / "synthetic_heldout.jsonl"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_queries(evaluate, ids, docs, metas):
    """평가 정답 chunk마다 질문 3개 (한 번 만들면 파일에 저장해 두고 다시 쓴다)"""
    if QUERIES.exists():
        return [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    make_dataset = load_module("make_dataset", ROOT / "train" / "make_dataset.py")
    held_out = sorted(make_dataset.load_eval_gold(metas, docs))
    todo = [(ids[i], docs[i]) for i in held_out]
    rows = []
    for start in range(0, len(todo), make_dataset.BATCH):
        for cid, queries in make_dataset.ask(todo[start:start + make_dataset.BATCH]).items():
            rows += [{"chunk_id": cid, "query": q} for q in queries]
    QUERIES.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return rows


def ranks(model_name, evaluate, rows, ids, docs, bm25):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    chunk_vectors = evaluate.embed_chunks(model, model_name, ids, docs)
    query_vectors = model.encode([QUERY_PREFIX + r["query"] for r in rows], normalize_embeddings=True)
    position = {cid: i for i, cid in enumerate(ids)}
    vector, hybrid = [], []
    for row, qv in zip(rows, query_vectors):
        gold = {position[row["chunk_id"]]}
        vector_order = list(np.argsort(-(chunk_vectors @ qv)))
        keyword_order = list(np.argsort(-bm25.get_scores(tokenize(row["query"]))))
        vector.append(evaluate.first_rank(vector_order, gold))
        hybrid.append(evaluate.first_rank(evaluate.hybrid(vector_order, keyword_order), gold))
    return vector, hybrid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    from rank_bm25 import BM25Okapi

    evaluate = load_module("evaluate", EVAL_DIR / "evaluate.py")
    ids, docs, metas = evaluate.load_chunks()
    rows = make_queries(evaluate, ids, docs, metas)
    bm25 = BM25Okapi([tokenize(doc) for doc in docs])
    cols = ["R@1", "R@3", "R@6", "R@10", "MRR@10"]
    lines = [f"질문 {len(rows)}개 (학습에서 뺀 chunk {len({r['chunk_id'] for r in rows})}개에 대해 LLM이 만든 질문)", "",
             "| 모델 | 검색 방식 | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for name in (EMBED_MODEL, args.model):
        vector, hybrid = ranks(name, evaluate, rows, ids, docs, bm25)
        for label, r in (("벡터", vector), ("하이브리드", hybrid)):
            row = evaluate.summarize(r)
            lines.append(f"| {name} | {label} | " + " | ".join(f"{row[c]:.3f}" for c in cols) + " |")
    report = "\n".join(lines) + "\n"
    (EVAL_DIR / "results" / "synthetic_check.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
