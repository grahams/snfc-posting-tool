FROM python:latest
LABEL org.opencontainers.image.source="https://github.com/grahams/snfc-posting-tool"

RUN echo 'deb [signed-by=/etc/apt/keyrings/hugo.gpg] https://hugo-apt.8hob.io latest main' | tee /etc/apt/sources.list.d/hugo.list
RUN mkdir -p /etc/apt/keyrings && wget -O /etc/apt/keyrings/hugo.gpg https://hugo-apt.8hob.io/signing-key
RUN apt-get update && apt-get install -y hugo

ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
