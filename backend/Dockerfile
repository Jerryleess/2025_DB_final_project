FROM python:3.13-slim

# 1. 複製 uv 執行檔
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

LABEL maintainer="boyan1001 <cby931001@gmail.com>"

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    # 預設 Gunicorn 參數
    PORT=8000 \
    WEB_CONCURRENCY=2 \
    THREADS=8 \
    TIMEOUT=120

WORKDIR /app

# 2. 安裝最小化系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 3. 安裝 Python 依賴（利用 Layer Cache）
# 先複製定義檔，只要這兩個檔案沒變，就不會重新安裝套件
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 4. 複製專案原始碼並處理權限
COPY . /app/
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

# 切換至非 root 使用者
USER appuser

# 5. 宣告 Port（僅供說明，不具實質轉發功能）
EXPOSE 8000

# 6. 使用 Shell 形式啟動 Gunicorn 以解析環境變數
# 這樣你在 docker run -e PORT=xxxx 時才會生效
CMD gunicorn --workers ${WEB_CONCURRENCY} \
             --threads ${THREADS} \
             --timeout ${TIMEOUT} \
             --bind 0.0.0.0:${PORT} \
             app:app