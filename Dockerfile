FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY . .

RUN uv sync --frozen --no-dev

EXPOSE 8088

CMD ["uv", "run", "--frozen", "--no-dev", "python", "main.py"]
