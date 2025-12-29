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
      default-libmysqlclient-dev \
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

# ENTRYPOINT + CMD
ENTRYPOINT ["gunicorn"]
CMD ["_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "180", "--graceful-timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-" ]