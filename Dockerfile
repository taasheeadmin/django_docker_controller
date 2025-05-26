FROM python:3.10-slim

RUN apt update && apt install vim -y

WORKDIR /code

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000
