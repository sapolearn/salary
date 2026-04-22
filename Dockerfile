FROM python:3.12-slim

WORKDIR /app

COPY app.py /app/app.py
COPY static /app/static

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD ["python", "app.py"]
