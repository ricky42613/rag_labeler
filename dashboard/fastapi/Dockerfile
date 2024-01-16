FROM tiangolo/uvicorn-gunicorn:python3.11

RUN mkdir /fastapi

COPY requirements.txt /fastapi

WORKDIR /fastapi

RUN pip install -r requirements.txt

COPY . /fastapi

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8888"]


EXPOSE 8888