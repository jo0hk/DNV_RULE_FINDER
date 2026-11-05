"""
eval/evaluate.py — 검색 정확도 측정

    평가용 질문(eval/questions.jsonl)마다 정답 조항이 검색 결과 몇 등에 나오는지 재서
    Recall@k(상위 k개 안에 정답이 있는 비율)와 MRR(정답 순위의 역수 평균)을 계산한다.
    벡터 검색 / 키워드 검색(BM25) / 하이브리드(서비스에서 실제로 쓰는 방식)를 따로 잰다.

    벡터 검색은 Chroma에 저장된 벡터 대신, 지정한 모델로 chunk를 다시 임베딩해 전수 계산한다.
    그래야 학습한 모델과 기존 모델을 같은 조건에서 비교할 수 있다. (임베딩은 eval/cache에 저장)

실행:  python eval/evaluate.py                                   (지금 쓰는 임베딩 모델)
       python eval/evaluate.py --model models/xxx --name finetuned  (학습한 모델)

결과:  eval/results/<name>.md   (요약 표)
       eval/results/<name>.json (질문별 순위)
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
from config import CANDIDATES, COLLECTION, DB_DIR, EMBED_MODEL, QUERY_PREFIX, TOP_K  # noqa: E402
from rag import tokenize  # noqa: E402

KS = (1, 3, TOP_K, 10)


def load_chunks():
    import chromadb
    collection = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION)
    data = collection.get(include=["documents", "metadatas"])
    return data["ids"], data["documents"], data["metadatas"]


def embed_chunks(model, model_name, ids, docs):
    """chunk 임베딩. 같은 모델·같은 chunk면 저장해 둔 것을 다시 쓴다"""
    key = hashlib.sha1(("\n".join(ids) + model_name).encode()).hexdigest()[:12]
    cache = EVAL_DIR / "cache" / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', model_name)}-{key}.npy"
    if cache.exists():
        return np.load(cache)
    print(f"chunk {len(docs)}개 임베딩 중 (모델: {model_name}) - 처음 한 번만 몇 분 걸립니다")
    vectors = model.encode(docs, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    cache.parent.mkdir(exist_ok=True)
    np.save(cache, vectors)
    return vectors


def gold_positions(question, metas, docs):
    """정답 조항이 들어 있는 chunk 위치들. 조항 하나가 여러 chunk에 걸칠 수 있다"""
    found = set()
    for gold in question["gold"]:
        pattern = re.compile(rf"(^|\n){re.escape(gold['clause'])}(\s|$)")
        for i, (meta, doc) in enumerate(zip(metas, docs)):
            ref = meta["ref"]
            if (ref == gold["ref"] or ref.startswith(gold["ref"] + " ")) and pattern.search(doc):
                found.add(i)
    return found


def hybrid(vector_order, keyword_order):
    """rag.search와 같은 방식: 각 검색의 상위 CANDIDATES개를 RRF로 합친다"""
    combined = {}
    for order in (vector_order[:CANDIDATES], keyword_order[:CANDIDATES]):
        for rank, i in enumerate(order):
            combined[i] = combined.get(i, 0) + 1 / (60 + rank)
    return sorted(combined, key=combined.get, reverse=True)


def first_rank(order, gold):
    for rank, i in enumerate(order, start=1):
        if i in gold:
            return rank
    return None


def summarize(ranks):
    n = len(ranks)
    row = {f"R@{k}": sum(1 for r in ranks if r and r <= k) / n for k in KS}
    row["MRR@10"] = sum(1 / r for r in ranks if r and r <= 10) / n
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=EMBED_MODEL, help="임베딩 모델 이름 또는 폴더")
    parser.add_argument("--name", default="baseline", help="결과 파일 이름")
    args = parser.parse_args()

    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer

    questions = [json.loads(line) for line in (EVAL_DIR / "questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ids, docs, metas = load_chunks()
    model = SentenceTransformer(args.model)
    chunk_vectors = embed_chunks(model, args.model, ids, docs)
    bm25 = BM25Okapi([tokenize(doc) for doc in docs])

    query_vectors = model.encode([QUERY_PREFIX + q["question"] for q in questions], normalize_embeddings=True)
    records, missing = [], []
    for q, qv in zip(questions, query_vectors):
        gold = gold_positions(q, metas, docs)
        if not gold:
            missing.append(q["id"])
            continue
        vector_order = list(np.argsort(-(chunk_vectors @ qv)))
        keyword_order = list(np.argsort(-bm25.get_scores(tokenize(q["question"]))))
        hybrid_order = hybrid(vector_order, keyword_order)
        records.append({
            "id": q["id"], "question": q["question"], "topic": q["topic"],
            "part": q["gold"][0]["ref"].split()[1],
            "gold": [f"{g['ref']} [{g['clause']}]" for g in q["gold"]],
            "vector": first_rank(vector_order, gold),
            "keyword": first_rank(keyword_order, gold),
            "hybrid": first_rank(hybrid_order, gold),
            "hybrid_top1": metas[int(hybrid_order[0])]["ref"],
        })
    if missing:
        raise SystemExit(f"정답 조항을 DB에서 찾지 못한 질문: {missing} (questions.jsonl의 ref/clause 확인)")

    methods = {"벡터 검색": "vector", "키워드 검색 (BM25)": "keyword", "하이브리드 (서비스 방식)": "hybrid"}
    table = {label: summarize([r[key] for r in records]) for label, key in methods.items()}
    by_part = {}
    for part in sorted({r["part"] for r in records}):
        ranks = [r["hybrid"] for r in records if r["part"] == part]
        by_part[part] = (len(ranks), summarize(ranks)[f"R@{TOP_K}"])
    misses = [r for r in records if not r["hybrid"] or r["hybrid"] > TOP_K]

    cols = [f"R@{k}" for k in KS] + ["MRR@10"]
    lines = [f"# 검색 정확도: {args.name}", "",
             f"- 임베딩 모델: `{args.model}`",
             f"- 평가 질문: {len(records)}개, 검색 대상 chunk: {len(ids)}개",
             f"- LLM에 넘기는 발췌문은 상위 {TOP_K}개이므로 **하이브리드 R@{TOP_K}**가 실제 서비스 정확도에 해당한다", "",
             "| 검색 방식 | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for label, row in table.items():
        lines.append(f"| {label} | " + " | ".join(f"{row[c]:.3f}" for c in cols) + " |")
    lines += ["", f"## Part별 하이브리드 R@{TOP_K}", "", "| Part | 질문 수 | R@6 |", "|---|---|---|"]
    lines += [f"| {part} | {n} | {r:.3f} |" for part, (n, r) in by_part.items()]
    lines += ["", f"## 상위 {TOP_K}개 안에 정답이 없던 질문 ({len(misses)}개)", "",
              "| id | 질문 | 정답 | 하이브리드 순위 | 하이브리드 1등 |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['question']} | {r['gold'][0]} | {r['hybrid'] or '-'} | {r['hybrid_top1']} |" for r in misses]
    report = "\n".join(lines) + "\n"

    out = EVAL_DIR / "results"
    out.mkdir(exist_ok=True)
    (out / f"{args.name}.md").write_text(report, encoding="utf-8")
    (out / f"{args.name}.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(report)
    print(f"저장: {out / (args.name + '.md')}")


if __name__ == "__main__":
    main()
