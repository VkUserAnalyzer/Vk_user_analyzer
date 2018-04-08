FROM python:3.6-jessie
ADD . /code
WORKDIR code
RUN pip install -r requirements.txt && \
    apt-get update && apt-get install -y curl python-software-properties && \
    curl -sL https://deb.nodesource.com/setup_9.x | bash - && \
    apt-get install -y nodejs && \
    cd rest_api && npm install && npm run build
CMD ["python3", "rest_api/manage.py runserver 0.0.0.0:8000"]