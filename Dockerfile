FROM python:3.11-slim
ENV PORT 8080
WORKDIR /

COPY requirements.txt /
RUN python -m pip install -r requirements.txt

COPY app.py utf8.db /
ADD templates /templates
ENTRYPOINT gunicorn -w 4 --bind=0.0.0.0:$PORT app:app
