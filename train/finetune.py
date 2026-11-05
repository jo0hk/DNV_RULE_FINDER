"""
train/finetune.py — 검색 임베딩 모델 미세조정

    train/data/queries.jsonl 의 (질문, 정답 chunk) 쌍으로 bge-small-en-v1.5를 추가 학습한다.

    손실 함수: MultipleNegativesRankingLoss
      한 배치(예: 32쌍) 안에서 질문마다 자기 정답 chunk와는 가깝게, 배치 안의 나머지 31개 chunk와는
      멀어지도록 학습한다. 같은 chunk가 한 배치에 두 번 들어가면 정답을 오답으로 배우게 되므로 막는다.

실행:  python train/finetune.py                               → models/bge-small-dnv
       python train/finetune.py --epochs 2 --output models/xxx
학습 뒤 평가:  python eval/evaluate.py --model models/bge-small-dnv --name finetuned
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import COLLECTION, DB_DIR, EMBED_MODEL, QUERY_PREFIX  # noqa: E402

DATA = ROOT / "train" / "data" / "queries.jsonl"


def load_pairs(limit=0):
    """(질문, 정답 chunk 본문) 쌍. 질문에는 검색할 때와 똑같이 QUERY_PREFIX를 붙인다"""
    import chromadb
    data = chromadb.PersistentClient(path=str(DB_DIR)).get_collection(COLLECTION).get(include=["documents"])
    text = dict(zip(data["ids"], data["documents"]))
    anchors, positives = [], []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for query in row["queries"]:
            anchors.append(QUERY_PREFIX + query)
            positives.append(text[row["chunk_id"]])
    if limit:
        anchors, positives = anchors[:limit], positives[:limit]
    return anchors, positives


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "models" / "bge-small-dnv"))
    parser.add_argument("--epochs", type=float, default=1)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-seq", type=int, default=256,
                        help="학습할 때 chunk를 자르는 최대 토큰 수. CPU에서는 짧을수록 빠르다 (검색할 때는 512 그대로)")
    parser.add_argument("--freeze-layers", type=int, default=6,
                        help="아래쪽 transformer 층 몇 개를 고정할지 (12층 중). 학습이 빨라지고 과적합이 줄어든다")
    parser.add_argument("--limit", type=int, default=0, help="앞에서부터 이 개수의 쌍만 (시험용)")
    args = parser.parse_args()

    from datasets import Dataset
    from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                       SentenceTransformerTrainingArguments, losses)
    from sentence_transformers.training_args import BatchSamplers

    anchors, positives = load_pairs(args.limit)
    dataset = Dataset.from_dict({"anchor": anchors, "positive": positives}).shuffle(seed=42)
    steps = int(len(dataset) / args.batch * args.epochs)
    print(f"학습 쌍 {len(dataset)}개, chunk {len(set(positives))}개, 배치 {args.batch}, 에폭 {args.epochs} → 약 {steps} step")

    model = SentenceTransformer(EMBED_MODEL)
    model.max_seq_length = args.max_seq
    if args.freeze_layers:
        bert = model[0].auto_model
        for module in [bert.embeddings, *bert.encoder.layer[:args.freeze_layers]]:
            for param in module.parameters():
                param.requires_grad = False
    output = Path(args.output)
    training_args = SentenceTransformerTrainingArguments(
        output_dir=str(output / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        learning_rate=args.lr,
        warmup_steps=max(1, int(steps * 0.1)),
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        logging_steps=max(1, steps // 20),
        save_strategy="no",
        report_to="none",
        seed=42,
    )
    trainer = SentenceTransformerTrainer(model=model, args=training_args, train_dataset=dataset,
                                         loss=losses.MultipleNegativesRankingLoss(model))
    started = time.time()
    trainer.train()
    minutes = (time.time() - started) / 60

    model.max_seq_length = 512      # 검색할 때는 원래 모델과 같은 길이로
    model.save(str(output))
    info = {"base_model": EMBED_MODEL, "pairs": len(dataset), "chunks": len(set(positives)), "epochs": args.epochs,
            "batch": args.batch, "lr": args.lr, "max_seq": args.max_seq, "freeze_layers": args.freeze_layers,
            "minutes": round(minutes, 1),
            "loss_log": [h for h in trainer.state.log_history if "loss" in h]}
    (output / "training_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"학습 {minutes:.1f}분, 저장: {output}")


if __name__ == "__main__":
    main()
