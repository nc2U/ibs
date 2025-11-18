# base image
FROM python:3.12
ENV PYTHONUNBUFFERED=1

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

# git safe.directory 설정 추가
RUN git config --global --add safe.directory '*'

EXPOSE 8000

# startup commands
ENTRYPOINT ["uwsgi"]
CMD ["--socket", ":8000", "--module", "_config.wsgi", "--py-autoreload", "1", "--logto", "/tmp/mylog.log", "--processes", "4", "--threads", "2", "--max-requests", "1000", "--harakiri", "60", "--buffer-size", "32768", "--vacuum", "--die-on-term"]
