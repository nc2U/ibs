# base image
FROM python:3.14
ENV PYTHONUNBUFFERED=1
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# set working directory
RUN mkdir -pv /app/django
WORKDIR /app/django

# copy required files
COPY requirements.txt .

# install dependencies
RUN apt update && apt upgrade -y && apt autoremove -y \
    && apt install python3-dev default-libmysqlclient-dev build-essential libpq-dev gcc -y \
    && apt install -y locales && locale-gen ko_KR.UTF-8 \
    && apt install fonts-nanum fonts-nanum-extra \
    && pip install --upgrade pip && pip install --upgrade setuptools \
    && pip install --trusted-host pypi.python.org -r requirements.txt

# git safe.directory 설정
RUN git config --global --add safe.directory '*'

EXPOSE 8000

# ENTRYPOINT + CMD
ENTRYPOINT ["uwsgi"]
CMD ["--socket", ":8000",\
     "--module", "_config.wsgi",\
     "--py-autoreload", "1",\
     "--logto", "/tmp/mylog.log",\
     "--post-buffering", "8388608",\
     "--buffer-size", "65535",\
     "--harakiri", "900",\
     "--http-timeout", "900",\
     "--socket-timeout", "900",\
     "--max-requests", "5000"
]
