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
WORKDIR /tmp/lib
COPY lib/jidouteki ./jidouteki

WORKDIR /app/lib/jidouteki-providers
COPY lib/jidouteki-providers .
RUN pip install -r requirements.txt

FROM base AS dev
RUN pip install -e /tmp/lib/jidouteki

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src src

CMD  ["flask", "--app", "src:app", "run", "--host", "0.0.0.0", "-p", "8080", "--debug"]

FROM base AS prod
WORKDIR /tmp/lib
RUN pip install ./jidouteki

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src src

CMD ["hypercorn", "--bind", "0.0.0.0:8080", "src:app"]

EXPOSE 8080