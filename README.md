## DNV 규정 RAG

> 개정 2026-10-12: 영어 전용으로 변경. 한국어 입력을 영어 검색어로 바꾸던 단계를 없애고,
> 한글이 들어간 문장은 받지 않도록 함. LLM 프롬프트, 답변, 화면 출력을 영어로 바꿈.
> 시연용 예시 문장을 영어로 교체함.

도면 수정 사항이나 문제 사항을 영어 문장으로 입력하면, DNV 선급 규정에서
관련 조항을 찾아 답변 + 근거 조항·페이지를 영어로 출력합니다.
한글이 들어간 문장은 받지 않습니다 (`English only` 안내만 출력).

| 파일 | 역할 |
|---|---|
| `ingest.py` | PDF → 조항 단위 chunk → 임베딩 → DB 저장 (처음 한 번만 실행) |
| `ask.py` | 영어 문장 입력 → 검색 → LLM 답변 + 출처 출력 |
| `llm.py` | LLM API 호출 (Claude / GPT / Gemini 중 키가 있는 것 사용) |
| `config.py` | 경로, 임베딩 모델, 검색 개수 등 설정 |
| `.env` | API 키를 적는 곳 |

## 실행 방법

VS Code에서 이 `dnv_rag` 폴더를 열고, 터미널에서 순서대로 실행합니다.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

```powershell
python ingest.py    
python ask.py     
```

`python ask.py "sentence"` 처럼 한 번만 물어볼 수도 있습니다.
API 키를 넣지 않고 실행하면 LLM 답변 없이 검색된 발췌문만 보여 줍니다.

## 동작 원리

```
[ingest.py]  PDF ─▶ 텍스트 추출 ─▶ 조항 단위 chunk ─▶ 임베딩 ─▶ Chroma DB
[ask.py]     입력 문장(영어) ─▶ 벡터 검색 + 키워드 검색
             ─▶ 순위 합치기(RRF) ─▶ 상위 6개 발췌문 + 문장을 LLM에 전달 ─▶ 답변 + 출처
```

1. 텍스트 추출 (PyMuPDF): 표지·목차·개정 이력 페이지와 바닥글·워터마크는 제외합니다.
2. 조항 단위 chunk: 글자 크기 13pt인 줄을 제목(`2 Special requirements`, `2.1 Bilge plating`)으로
   인식해 제목이 바뀔 때마다 자르고, 길면 조항(`2.1.3`) 경계에서 약 1,000자 단위로 나눕니다.
   각 chunk 첫 줄에 `DNV-RU-SHIP Pt.3 Ch.6 Sec.4 [2.1] | 장 제목 > 절 제목 > ...` 을 붙여
   어느 문서의 어느 조항인지 알 수 있게 했습니다.
3. 임베딩 (bge-small-en-v1.5, 로컬 실행): chunk를 384차원 벡터로 바꿔 Chroma에 저장합니다.
4. 검색: 문서와 임베딩 모델이 영어 전용이라 입력도 영어만 받습니다. 입력 문장을 그대로 검색어로 써서,
   의미가 비슷한 chunk를 찾는 벡터 검색과 같은 단어가 들어 있는 chunk를 찾는 키워드 검색(BM25)을 함께 씁니다.
   조항 번호·강재 등급처럼 정확한 단어가 중요한 규정 문서에서는 둘을 합치는 편이 안정적입니다.
5. 답변 생성: "발췌문에 있는 내용만 쓰고, 없으면 못 찾았다고 말하고, 근거 조항을 표시하고, 영어로 답하라"고 지시합니다.

## 시연용 예시 문장

아래 문장으로 검색(벡터 + 키워드, RRF)했을 때 해당 조항이 든 chunk가 LLM에 넘기는 상위 6개 안에
아래 순위로 나오는 것을 확인했습니다 (2026-10-12, LLM 답변 단계는 제외).

| 입력 문장 | 찾아야 하는 조항 | 순위 |
|---|---|---|
| Emergency towing arrangement SWL changed to 1,000 kN for a 60,000 dwt oil tanker | Pt.5 Ch.5 Sec.2 [2.2.3] | 1 |
| Bilge plate thickness modified to be thinner than the adjacent bottom plate | Pt.3 Ch.6 Sec.4 [2.1.1] | 2 |
| Inner bottom plate below a vertically corrugated bulkhead without lower stool is not Z-grade steel | Pt.5 Ch.5 Sec.2 [2.1.2] | 1 |
| Non-destructive testing omitted after weld repair of a copper alloy casting | Pt.2 Ch.2 Sec.11 [1.13.6] | 1 |
