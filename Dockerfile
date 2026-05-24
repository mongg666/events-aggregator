FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install uv && uv pip install --system -r pyproject.toml
COPY . .
RUN chmod +x run.sh
CMD ["./run.sh"]