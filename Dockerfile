FROM python:3.10

COPY . /

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "80"]
