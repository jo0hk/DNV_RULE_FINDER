# 서버 배포용 이미지 (Google Cloud Run). 로컬에서 쓸 때는 필요 없다: README의 "실행 방법" 참고
#
# chroma_db 폴더를 이미지 안에 넣으므로, 빌드하기 전에 python ingest.py로 DB를 만들어 두어야 한다.
# 이미지에는 DNV 규정 본문이 들어 있으니 공개 저장소(Docker Hub 등)에 올리지 않는다.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# torch는 GPU 없는 CPU 전용판을 먼저 깔아 이미지 크기를 줄인다
RUN pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

# 임베딩 모델을 이미지에 넣어 두고, 서버가 뜰 때는 인터넷에서 다시 받지 않게 한다
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
ENV HF_HUB_OFFLINE=1

COPY config.py llm.py rag.py server.py ./
COPY web ./web
COPY chroma_db ./chroma_db

# Cloud Run은 PORT 환경 변수로 포트를 알려 준다
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
