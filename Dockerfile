FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7-alpine3.8

RUN apk add --no-cache openssl-dev libffi-dev gcc musl-dev make

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV MODULE_NAME="scvmmapi.main"
ENV PORT=5555
EXPOSE 5555

COPY . /app

