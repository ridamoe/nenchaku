# FROM python:3.12 AS chrome

# # Install google chrome
# RUN apt-get update && apt-get install -y \
#     wget \
#     gnupg \
#     software-properties-common

# RUN wget https://dl-ssl.google.com/linux/linux_signing_key.pub -O /tmp/google.pub
# RUN gpg --no-default-keyring --keyring /etc/apt/keyrings/google-chrome.gpg --import /tmp/google.pub
# RUN sh -c "echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list"
# RUN apt-get update
# RUN apt-get install -y google-chrome-stable

FROM python:3.12 AS base
RUN --mount=type=bind,source=./lib/jidouteki/,target=/tmp/jidouteki \
pip install /tmp/jidouteki

RUN --mount=type=bind,source=./lib/parsers/,target=/tmp/parsers \
pip install -r /tmp/parsers/requirements.txt

WORKDIR /app/lib/parsers
COPY lib/parsers/parsers .
ENV PARSERS_DIR=/app/lib/parsers

FROM base AS app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src src

FROM app AS dev
CMD  ["flask", "--app", "src:app", "run", "--host", "0.0.0.0", "-p", "8080", "--debug"]

FROM app AS prod
CMD ["hypercorn", "--bind", "0.0.0.0:8080", "src:app"]

EXPOSE 8080