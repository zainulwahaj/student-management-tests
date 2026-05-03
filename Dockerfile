FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-liberation \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

WORKDIR /tests

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tests/reports

CMD ["pytest", "-v", "--tb=native", \
     "--html=/tests/reports/report.html", \
     "--self-contained-html", \
     "--junitxml=/tests/reports/junit.xml"]
