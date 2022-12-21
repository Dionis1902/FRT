FROM python:3.10

ADD . /files
WORKDIR /files

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]