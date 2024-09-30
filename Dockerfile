FROM python:3.10-slim
WORKDIR /app
COPY ./Bot /app
VOLUME [ "/data" ]
RUN pip install --no-cache-dir discord pandas bs4 requests python-dotenv
CMD ["python3","main.py"]
