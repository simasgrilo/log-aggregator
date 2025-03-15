FROM python:3.12
WORKDIR /app
RUN pip install -U pip
RUN apt-get update
RUN pip install poetry
RUN python -m venv /venv
COPY . /app/
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "LogAggregator:app"]