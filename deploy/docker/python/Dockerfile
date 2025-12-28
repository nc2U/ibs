# ========================================
# Stage 1: Builder
# ========================================
FROM python:3.12 AS builder

ENV PYTHONUNBUFFERED=1

# locales 설치 및 설정
RUN apt-get update \
 && apt-get install -y locales \
 && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen \
 && update-locale LANG=ko_KR.UTF-8

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# set working directory
RUN mkdir -pv /app/django
WORKDIR /app/django

# install build dependencies
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
 && apt-get autoremove -y

# copy requirements and install Python dependencies
COPY deploy/docker/python/requirements.txt .
RUN pip install --upgrade pip setuptools \
 && pip install --trusted-host pypi.python.org -r requirements.txt

# copy entire Django application source code
COPY app/django/ .

# collect static files (no database connection required)
# Using DJANGO_SETTINGS_MODULE to ensure proper settings
RUN python manage.py collectstatic --noinput --clear

# ========================================
# Stage 2: Runtime
# ========================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# locales 설치 및 설정
RUN apt-get update \
 && apt-get install -y locales git \
 && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen \
 && update-locale LANG=ko_KR.UTF-8 \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# install runtime dependencies only
RUN apt-get update \
 && apt-get install -y \
      default-libmysqlclient-dev \
      libpq-dev \
      fonts-nanum \
      fonts-nanum-extra \
      libmagic1 \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# set working directory
RUN mkdir -pv /app/django
WORKDIR /app/django

# copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# copy Django application source and collected static files from builder
COPY --from=builder /app/django /app/django

# git safe.directory 설정 (for work app integration)
RUN git config --global --add safe.directory '*'

# Note: .env file will be mounted from NFS at runtime
# Do NOT copy .env file into the image

EXPOSE 8000

# ENTRYPOINT + CMD
ENTRYPOINT ["gunicorn"]
CMD ["_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "180", "--graceful-timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-"]
