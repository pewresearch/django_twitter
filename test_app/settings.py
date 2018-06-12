import os, pwd, sys
from contextlib import closing
from django.db import models


sys.path.append("/Users/pvankessel/workspace/pewhooks")
sys.path.append("/opt/repos/api_hooks/pewhooks")

##### FILE PATHS

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..").decode('utf-8')).replace('\\', '/')
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)).decode('utf-8')).replace('\\', '/')

MEDIA_ROOT = os.path.abspath(os.path.join(APP_ROOT, "media").decode('utf-8')).replace('\\', '/')
TEMPLATE_ROOT = os.path.abspath(os.path.join(APP_ROOT, "templates").decode('utf-8')).replace('\\', '/')
FILE_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "files").decode('utf-8')).replace('\\', '/')
CACHE_ROOT = os.path.abspath(os.path.join(FILE_ROOT, "cache").decode('utf-8')).replace('\\', '/')
OUTPUT_ROOT = os.path.abspath(os.path.join(FILE_ROOT, "output").decode('utf-8')).replace('\\', '/')
STATIC_ROOT = os.path.abspath(os.path.join(APP_ROOT, "static").decode('utf-8')).replace('\\', '/')


##### BASIC SITE CONFIG

SITE_NAME = 'test_app'
DEBUG = True
SITE_ID = 1
TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
USE_TZ = False
ADMINS = (
    ('Galen Stocking', 'gstocking@pewresearch.org'),
    ('Patrick van Kessel', 'pvankessel@pewresearch.org'),
)
MANAGERS = ADMINS
WSGI_APPLICATION = 'test_app.wsgi.application'
SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer'
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware'
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.redirects',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'django.contrib.admindocs',
    "django_twitter",
    'test_app',
)


##### DATABASE SETTINGS

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'HOST':     'localhost',
        'NAME':     'test_db',
        'USER':     'postgres',
        'PASSWORD': 'test',
        'PORT':     ''
    }
}
SITE_READ_ONLY = False


##### DJANGO_COMMANDER SETTINGS

# DJANGO_COMMANDER_COMMAND_FOLDERS = [
#     os.path.abspath(os.path.join(APP_ROOT, "commands").decode('utf-8')).replace('\\', '/')
# ]

##### URL AND TEMPLATE SETTINGS

ROOT_URLCONF = 'test_app.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ]
        }
    },
]


##### STATIC MEDIA SETTINGS

MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "static"),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


##### SITE SECURITY SETTINGS

SECRET_KEY = "12345"
ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


##### AUTHENTICATION SETTINGS

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"
LOGIN_ERROR_URL = "/login"
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


##### LOGGING SETTINGS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
             'level': 'DEBUG',
             'class': 'logging.FileHandler',
             'filename': '/var/log/atpopen.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
LOGGING_CONFIG = None

##### DJANGO_FACEBOOK SETTINGS

TWITTER_PROFILE_MODEL = "TwitterProfile"
TWEET_MODEL = "Tweet"
BOTOMETER_SCORE_MODEL = "BotometerScore"
TWITTER_RELATIONSHIP_MODEL = "TwitterRelationship"
TWITTER_HASHTAG_MODEL = "TwitterHashtag"
TWITTER_PLACE_MODEL = "TwitterPlace"