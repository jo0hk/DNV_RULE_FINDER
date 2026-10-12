## DNV 규정 RAG

> 개정 2026-10-12: 영어 전용으로 변경. 한국어 입력을 영어 검색어로 바꾸던 단계를 없애고,
> 한글이 들어간 문장은 받지 않도록 함. LLM 프롬프트, 답변, 화면 출력을 영어로 바꿈.
> 시연용 예시 문장을 영어로 교체함.
>
> 개정 2026-10-12 (2): 웹 화면 추가. FastAPI 서버(`server.py`)와 화면(`web/`)을 넣고,
> 검색·답변 코드를 `ask.py`에서 `rag.py`로 옮겨 터미널과 웹이 함께 쓰도록 함. `.env.example` 추가.
>
> 개정 2026-10-13: 화면 디자인 교체. 인터넷 공개 배포 지원 추가(화면은 GitHub Pages, 서버는 Google Cloud Run).
> `Dockerfile`, Pages 워크플로, `web/config.js`를 넣고, 서버에 다른 주소 허용(CORS), LLM 답변 하루 상한,
> 원문 PDF가 없을 때 `Open PDF` 숨김을 추가함. `requirements.txt`의 버전을 고정함.

> 개정 2026-10-13 (2): 저장소 이름이 `DNV_RULE_FINDER`로 바뀌어 데모 주소를 고침.
> `.env.example`을 없애고, `.env`에 적을 내용을 실행 방법에 직접 적음.

**데모: https://jo0hk.github.io/DNV_RULE_FINDER/** (서버가 쉬고 있었다면 첫 검색은 1분 가까이 걸릴 수 있습니다)

도면 수정 사항이나 문제 사항을 영어 문장으로 입력하면, DNV 선급 규정에서
관련 조항을 찾아 답변 + 근거 조항·페이지를 영어로 출력합니다.
한글이 들어간 문장은 받지 않습니다 (`English only` 안내만 출력).
웹 화면과 터미널 두 가지로 쓸 수 있습니다.

| 파일 | 역할 |
|---|---|
| `ingest.py` | PDF → 조항 단위 chunk → 임베딩 → DB 저장 (처음 한 번만 실행) |
| `rag.py` | 검색(벡터 + 키워드)과 LLM 답변 생성. 웹과 터미널이 함께 씀 |
| `server.py` | 웹 서버: 화면(`web/`)과 API(`/api/search`, `/api/answer` 등)를 띄움 |
| `web/` | 화면 (`index.html`, `style.css`, `app.js`). 빌드 과정 없이 그대로 열림. `config.js`에 배포 서버 주소를 적음 |
| `Dockerfile` | 서버 배포용 이미지 (Cloud Run) |
| `.github/workflows/pages.yml` | `web/`을 GitHub Pages에 올리는 워크플로 |
| `ask.py` | 터미널용: 영어 문장 입력 → 답변 + 출처 출력 |
| `llm.py` | LLM API 호출 (Claude / GPT / Gemini 중 키가 있는 것 사용) |
| `config.py` | 경로, 임베딩 모델, 검색 개수 등 설정 |
| `.env` | API 키를 적는 곳 (직접 만듦, git에는 올리지 않음) |

DNV 규정 PDF와 `chroma_db`(규정 원문이 들어 있음)는 저장소에 포함하지 않습니다.
PDF는 이 폴더와 같은 위치의 `DNV` 폴더에 두거나, `.env`의 `DOCS_DIR`로 위치를 지정합니다.

## 실행 방법

VS Code에서 이 `dnv_rag` 폴더를 열고, 터미널에서 순서대로 실행합니다.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

이 폴더에 `.env` 파일을 만들고 LLM API 키를 하나 적습니다. 셋 중 하나만 있으면 되고,
넣지 않으면 LLM 답변 없이 검색된 발췌문만 보여 줍니다.

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
```

필요하면 같은 파일에 아래 값도 적을 수 있습니다.

| 이름 | 뜻 |
|---|---|
| `LLM_PROVIDER` | 키를 여러 개 넣었을 때 쓸 회사 (`anthropic` / `openai` / `gemini`) |
| `LLM_MODEL` | 모델 이름. 없으면 `llm.py`의 기본 모델 |
| `DOCS_DIR` | DNV 규정 PDF가 있는 폴더. 없으면 이 폴더와 같은 위치의 `DNV` 폴더 |

```powershell
python ingest.py
```

웹 화면으로 쓰기 (브라우저에서 http://127.0.0.1:8000 을 엽니다. 모델을 불러오느라 서버가 뜨는 데 수십 초 걸립니다):

```powershell
uvicorn server:app --port 8000
```

터미널에서 쓰기:

```powershell
python ask.py
```

`python ask.py "sentence"` 처럼 한 번만 물어볼 수도 있습니다.

## 웹 화면

- 문장을 입력하면 출처 카드(조항 번호, 경로, Edition, 페이지, 발췌문)가 먼저 나오고, 이어서 LLM 답변이 나옵니다.
- 답변의 `[1]` 같은 번호를 누르면 해당 출처 카드로 이동합니다.
- 출처 카드의 `Open PDF`는 규정 원문 PDF를 해당 페이지에서 엽니다 (수식·그림 확인용).
- 질문 기록은 브라우저에만 저장됩니다.
- 위 명령으로 띄운 서버는 이 컴퓨터(`127.0.0.1`)에서만 접속됩니다.

## 인터넷에 공개하기

화면은 GitHub Pages에, 서버는 Google Cloud Run에 올립니다. 서버는 안 쓸 때 꺼져 있다가 첫 요청에 켜집니다.

```
https://jo0hk.github.io/DNV_RULE_FINDER/  (web/ 폴더, GitHub Pages)
        │  /api/search, /api/answer
        ▼
Cloud Run 서버 (Dockerfile: server.py + 임베딩 모델 + chroma_db)
```

1. 서버 배포. Google Cloud 프로젝트와 결제 계정, `gcloud` CLI가 필요합니다. `chroma_db`가 만들어져 있어야 합니다.

   ```powershell
   gcloud run deploy dnv-rule-finder --source . --region asia-northeast1 --memory 1Gi --cpu 1 --cpu-boost --max-instances 1 --allow-unauthenticated --set-env-vars "ALLOWED_ORIGINS=https://jo0hk.github.io,ANSWER_LIMIT_PER_DAY=100"
   ```

   LLM API 키는 Cloud Run 콘솔의 서비스 > 새 버전 수정 및 배포 > 변수 및 보안 비밀에서 `GEMINI_API_KEY`로 넣습니다.
2. 배포가 끝나면 나오는 서버 주소를 `web/config.js`의 `CLOUD_RUN_URL`에 적고 커밋·푸시합니다.
3. GitHub 저장소 Settings > Pages > Source를 `GitHub Actions`로 바꿉니다. `web/`이 바뀔 때마다 자동으로 올라갑니다.

공개 서버에서 달라지는 점:

- 원문 PDF는 올리지 않으므로 `Open PDF` 링크가 보이지 않습니다.
- LLM 답변은 `ANSWER_LIMIT_PER_DAY`번까지만 만듭니다(API 요금 보호). 횟수는 서버 메모리에 세므로 서버가 꺼졌다 켜지면 다시 0부터 셉니다.
- `ALLOWED_ORIGINS`에 적은 주소의 화면만 서버에 요청할 수 있습니다.
- 배포 이미지에는 규정 본문(`chroma_db`)이 들어가고, 검색 결과로 발췌문이 누구에게나 나갑니다.

## 동작 원리

```
[ingest.py]  PDF ─▶ 텍스트 추출 ─▶ 조항 단위 chunk ─▶ 임베딩 ─▶ Chroma DB
[rag.py]     입력 문장(영어) ─▶ 벡터 검색 + 키워드 검색
             ─▶ 순위 합치기(RRF) ─▶ 상위 6개 발췌문 + 문장을 LLM에 전달 ─▶ 답변 + 출처
[server.py]  화면(web/) ◀─▶ /api/search (발췌문) , /api/answer (발췌문 + 답변) ◀─▶ rag.py
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
