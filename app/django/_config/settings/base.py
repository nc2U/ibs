"""
Django settings for _config project.

Generated by 'django-admin startproject' using Django 4.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import string
import random
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace(
    '\\', '')
SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1

APPEND_SLASH = True

AUTH_USER_MODEL = 'accounts.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
]

INSTALLED_APPS += [  # plugin
    'import_export',
    'rangefilter',
    'widget_tweaks',
    'django_markdown2',
    'mdeditor',
    'storages',
    'mathfilters',
    'rest_framework',
    'rest_framework_simplejwt',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap4',
]

INSTALLED_APPS += [  # app
    'apiV1.apps.ApiV1Config',
    'accounts.apps.AccountsConfig',
    'book.apps.BookConfig',
    'board.apps.BoardConfig',
    'cash.apps.CashConfig',
    'company.apps.CompanyConfig',
    'contract.apps.ContractConfig',
    'docs.apps.DocsConfig',
    'ibs.apps.IbsConfig',
    'items.apps.ItemsConfig',
    'notice.apps.NoticeConfig',
    'payment.apps.PaymentConfig',
    'project.apps.ProjectConfig',
    'work.apps.WorkConfig',
    '_excel.apps.ExcelConfig',
    '_pdf.apps.PdfConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = '_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = '_config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DB_TYPE = os.getenv('DATABASE_TYPE') or 'mariadb'
DB_ENGINE = 'mysql' if DB_TYPE == 'mariadb' else 'postgresql'
DEFAULT_DB_PORT = '3306' if DB_TYPE == 'mariadb' else '5432'
DB_PORT = DEFAULT_DB_PORT  # os.getenv('DATABASE_PORT') or DEFAULT_DB_PORT
MASTER_HOST = DB_TYPE if 'local' in os.getenv('DJANGO_SETTINGS_MODULE') \
    else f'{DB_TYPE}-0.{os.getenv("DB_SERVICE_NAME")}.{os.getenv("NAMESPACE")}.svc.cluster.local'
DEFAULT_OPTIONS = {
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",  # 초기 명령어 설정
    'charset': 'utf8mb4',  # 캐릭터셋 설정
    'connect_timeout': 10,  # 연결 타임아웃 설정
} if DB_TYPE == 'mariadb' else {'connect_timeout': 10, }
SLAVE_OPTIONS = {'charset': 'utf8mb4', 'connect_timeout': 10, } if DB_TYPE == 'mariadb' else {'connect_timeout': 10, }
DATABASES = {
    'default': {
        'ENGINE': f'django.db.backends.{DB_ENGINE}',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        "DEFAULT-CHARACTER-SET": 'utf8',
        'HOST': MASTER_HOST,
        'PORT': DB_PORT,
        'OPTIONS': DEFAULT_OPTIONS,
    },
    'slave1': {
        'ENGINE': f'django.db.backends.{DB_ENGINE}',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        "DEFAULT-CHARACTER-SET": 'utf8',
        'HOST': f'{DB_TYPE}-1.{os.getenv("DB_SERVICE_NAME")}.{os.getenv("NAMESPACE")}.svc.cluster.local',
        'PORT': DB_PORT,
        'OPTIONS': SLAVE_OPTIONS,
    },
    'slave2': {
        'ENGINE': f'django.db.backends.{DB_ENGINE}',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        "DEFAULT-CHARACTER-SET": 'utf8',
        'HOST': f'{DB_TYPE}-2.{os.getenv("DB_SERVICE_NAME")}.{os.getenv("NAMESPACE")}.svc.cluster.local',
        'PORT': DB_PORT,
        'OPTIONS': SLAVE_OPTIONS,
    }
}

DATABASE_ROUTERS = [] if 'local' in os.getenv('DJANGO_SETTINGS_MODULE') \
    else [BASE_DIR / "_config.database_router.MasterSlaveRouter"]

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_TZ = True

USE_I18N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = None  # os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_REGION = 'ap-northeast-2'
AWS_S3_CUSTOM_DOMAIN = ''  # f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com'
# AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400', }
# AWS_DEFAULT_ACL = 'public-read'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = (BASE_DIR / '_assets',)

# DEFAULT_FILE_STORAGE = '_config.asset_storage.MediaStorage'

# 각 media 파일에 관한 URL prefix
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/' if AWS_STORAGE_BUCKET_NAME else 'media/'
MEDIA_ROOT = BASE_DIR / 'media'  # 업로드된 파일을 저장할 디렉토리 경로

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_LOGIN_METHODS = ['email']
ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password*']

# EMAIL SETTINGS
DOMAIN_HOST = os.getenv('DOMAIN_HOST', 'http://localhost/')  # ex: 'https://abc.com/'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')  # 'your-smtp-server.com'
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # 'your accessId or accessEmail'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # 'your-email-password'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')  # 'your-email@example.com'

CRISPY_TEMPLATE_PACK = "bootstrap4"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

REST_FRAMEWORK = {
    # 'DEFAULT_PAGINATION_CLASS': 'apiV1.pagination.LimitOffsetPaginationWithMaxLimit',
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PAGINATION_CLASS': 'apiV1.pagination.PageNumberPaginationCustomBasic',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.backends.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '5000/hour',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=28),
    'ROTATE_REFRESH_TOKENS': False,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

MDEDITOR_CONFIGS = {
    'default': {
        'language': 'en',
        'width': '100%',  # Custom edit box width
        'height': 500,  # Custom edit box height
        'toolbar': ["undo", "redo", "|",
                    "bold", "del", "italic", "quote", "ucwords", "uppercase", "lowercase", "|",
                    "h1", "h2", "h3", "h5", "h6", "|",
                    "list-ul", "list-ol", "hr", "|",
                    "link", "reference-link", "code", "preformatted-text", "code-block", "table", "datetime", "emoji",
                    "html-entities", "pagebreak", "|", "goto-line", "|", "help", "info",
                    "||", "preview", "watch", "fullscreen"],  # custom edit box toolbar
        'upload_image_formats': ["jpg", "jpeg", "gif", "png"],  # image upload format type
        'image_folder': 'mke_images',  # image save the folder name
        'theme': 'default',  # edit box theme, dark / default
        'preview_theme': 'default',  # Preview area theme, dark / default
        'editor_theme': 'default',  # edit area theme, pastel-on-dark / default
        'toolbar_autofixed': True,  # Whether the toolbar capitals
        'search_replace': True,  # Whether to open the search for replacement
        'emoji': True,  # whether to open the expression function
        'tex': True,  # whether to open the tex chart function
        'flow_chart': True,  # whether to open the flow chart function
        'sequence': True,  # Whether to open the sequence diagram function
        'watch': True,  # Live preview
        'lineWrapping': True,  # lineWrapping
        'lineNumbers': True  # lineNumbers
    }
}
APP_ORDER = [
    'company',
    'work',
    'project',
    'items',
    'payment',
    'contract',
    'cash',
    'ibs',
    'notice',
    'docs',
    'board',
    'accounts',
    'book',
]
