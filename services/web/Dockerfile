###########
# BUILDER #
###########

# pull official base image
FROM python:3.9.21-slim as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl ca-certificates

# install the tailwind standalone cli
ARG TAILWIND_VERSION=v4.3.3
ARG TAILWIND_SHA256_AMD64=dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a
ARG TAILWIND_SHA256_ARM64=55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195
RUN case "$(dpkg --print-architecture)" in \
        amd64) arch=x64; sha=$TAILWIND_SHA256_AMD64 ;; \
        arm64) arch=arm64; sha=$TAILWIND_SHA256_ARM64 ;; \
        *) echo "Unsupported architecture" >&2; exit 1 ;; \
    esac && \
    curl -fsSL -o /usr/local/bin/tailwindcss \
        "https://github.com/tailwindlabs/tailwindcss/releases/download/$TAILWIND_VERSION/tailwindcss-linux-$arch" && \
    echo "$sha  /usr/local/bin/tailwindcss" | sha256sum -c - && \
    chmod +x /usr/local/bin/tailwindcss

# lint
RUN pip install --upgrade pip
RUN pip install flake8==3.9.1
COPY . .
RUN flake8 --ignore=E501,W503,F401,E126 .

# build css
RUN tailwindcss -i project/styles/app.css -o project/assets/app.css --minify

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.9.21-slim

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME
COPY --from=builder /usr/src/app/project/assets/app.css $APP_HOME/project/assets/app.css

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

