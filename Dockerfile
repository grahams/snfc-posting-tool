FROM python:latest
ADD . /project
WORKDIR /project
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
