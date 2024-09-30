FROM python:3.10-slim
WORKDIR /app
COPY . /app
VOLUME [ "/data" ]
RUN pip install --no-cache-dir discord pandas bs4 requests asyncio dotenv datetime re json pathlib 
CMD ["python3","main.py"]