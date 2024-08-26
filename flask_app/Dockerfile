FROM tiangolo/uwsgi-nginx-flask:python3.11

ADD * /app

RUN pip install -r /app/requirements.txt

EXPOSE 9090

ENTRYPOINT ["uwsgi", "--ini", "/app/app.ini"]