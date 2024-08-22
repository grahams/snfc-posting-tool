FROM python:latest
LABEL org.opencontainers.image.source="https://github.com/grahams/snfc-posting-tool"

ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
