# base image
FROM python:3.14

# Python 기본 설정
ENV PYTHONUNBUFFERED=1

# -------------------------
#   UTF-8 Locale 적용
# -------------------------
# C.UTF-8 → ko_KR.UTF-8 이 더 안정적
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# set UTF-8 locale
RUN apt update && apt install -y locales \
    && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8

# -------------------------------------------------------
#   WORKDIR
# -------------------------------------------------------
RUN mkdir -pv /app/django
WORKDIR /app/django

# -------------------------------------------------------
#    Dependencies
# -------------------------------------------------------
COPY requirements.txt .

RUN apt update && apt upgrade -y && apt autoremove -y \
    && apt install python3-dev default-libmysqlclient-dev build-essential libpq-dev gcc -y \
    && apt install fonts-nanum fonts-nanum-extra -y \
    && pip install --upgrade pip && pip install --upgrade setuptools \
    && pip install --trusted-host pypi.python.org -r requirements.txt

# Git safe.directory 설정
RUN git config --global --add safe.directory '*'

# -------------------------------------------------------
#    expose
# -------------------------------------------------------
EXPOSE 8000

# -------------------------------------------------------
#    uwsgi startup
#    (UTF-8 환경 강제 → 이것이 핵심)
# -------------------------------------------------------
ENTRYPOINT ["uwsgi"]

CMD [
     "--env", "LANG=ko_KR.UTF-8",
     "--env", "LC_ALL=ko_KR.UTF-8",
     "--env", "LANGUAGE=ko_KR:UTF-8",

     "--socket", ":8000",
     "--module", "_config.wsgi",

     "--py-autoreload", "1",
     "--logto", "/tmp/mylog.log",
     "--post-buffering", "8388608",
     "--buffer-size", "65535",

     "--harakiri", "900",
     "--http-timeout", "900",
     "--socket-timeout", "900",
     "--max-requests", "5000"
]
