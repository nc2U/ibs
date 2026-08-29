# base image
FROM python:3.14
ENV PYTHONUNBUFFERED=1

# locales 설치 및 설정
RUN apt-get update \
 && apt-get install -y locales \
 && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen \
 && update-locale LANG=ko_KR.UTF-8 \

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# set working directory
RUN mkdir -pv /app/django
WORKDIR /app/django

# copy required files
COPY requirements.txt .

# install dependencies
RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y \
      python3-dev \
      build-essential \
      libpq-dev \
      gcc \
      fonts-nanum \
      fonts-nanum-extra \
      libmagic1 \
 && apt-get autoremove -y \
 && pip install --upgrade pip setuptools \
 && pip install --trusted-host pypi.python.org -r requirements.txt

# git safe.directory 설정
RUN git config --global --add safe.directory '*'

EXPOSE 8000

# ASGI Server (Daphne: HTTP + WebSocket Channels 동시 완벽 지원)
ENTRYPOINT ["daphne"]
CMD ["-b", "0.0.0.0", "-p", "8000", "_config.asgi:application"]