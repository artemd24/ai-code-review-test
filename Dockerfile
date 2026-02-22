FROM python:3.8-slim as compile-image

RUN pip3 install matplotlib
RUN pip3 install -U numpy

COPY ./requirements.txt /app/
COPY app/ /app/
WORKDIR /app

RUN python3 -m venv venv
RUN venv/bin/python3 -m pip install --upgrade pip

RUN venv/bin/pip3 install --no-cache-dir --requirement requirements.txt

FROM python:3.8-alpine as runtime-image

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_PORT=5000
COPY --from=compile-image /app /app

ENTRYPOINT ["app/venv/bin/python3", "-m", "app"]