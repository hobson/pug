"""
Django settings for crawlnmine project.

TODO:
    https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
"""

import os
import sys
import string
import random

SHELL_PLUS_PRE_IMPORTS = (
    # ('module.submodule1', ('class1', 'function2')),
    # ('module.submodule2', 'function3'),
    ('invest.models', '*'),
    # 'module.submodule4'
)


def env(var_name, default=False):
    """ Get the environment variable. If not found use a default or False, but print to stderr a warning about the missing env variable."""
    try:
        value = os.environ[var_name]
        if str(value).strip().lower() in ['false', 'f', 'no', 'off' '0', 'none', 'null', '', ]:
            return None
        return value
    except:
        from traceback import format_exc
        msg = "Unable to find the %s environment variable.\nUsing the value %s (the default) instead.\n" % (var_name, default)
        sys.stderr.write(format_exc())
        sys.stderr.write(msg)
        return default


# path to the folder containing this file (settings)
PROJECT_SETTINGS_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

# path to the folder created with djangoadmin startproject (e.g. ~/src/pug/pug/crawlnmine)
BASE_DIR = os.path.realpath(os.path.join(PROJECT_SETTINGS_PATH, '..', '..'))

# Find out what this Project is called (its containing folder name, e.g. 'crawlnmine' ) so these settings are reusable by just moving them to another folder
PROJECT_NAME = os.path.basename(BASE_DIR)

# the folder conataining the django project because "peer" projects may be django apps we want to install
ROOT_PROJECT_PATH = os.path.realpath(os.path.join(BASE_DIR, '..'))

# Because the django apps we want in INSTALLED_APPS are at the same level of ths project they are "external"
# So, add their containing folder to the python path here
if ROOT_PROJECT_PATH not in sys.path:
    sys.path.insert(1, ROOT_PROJECT_PATH)


# If there's an environment variable containing a secret key it'll be used, otherwise a random one will be generated
NEW_SECRET_KEY = ''.join(random.choice(string.printable) for _ in range(32))
SECRET_KEY = env("DJANGO_SECRET_KEY", default=NEW_SECRET_KEY)  # os.urandom(32) isn't terminal printable

# Heroku: Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(env("DJANGO_DEBUG", default=False))

TEMPLATE_DEBUG = DEBUG


# ALLOWED_HOSTS = []
# Heroku: Allow all hosts
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',

    'gunicorn',  # adds run_gunicorn command

    PROJECT_NAME, # to provide access to crawlnmine/static and crawlnmine/templates
    'invest',     # draws line plots of financial data and predicts futures finance statists

    # 'crawler',  # crawls wikipedia using Scrapy
    # 'miner',    # mines databases with NLP and draws line/bar plots
    # 'agile',    # jira command-line tool to create tickets?
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = PROJECT_NAME + '.urls'

WSGI_APPLICATION = PROJECT_NAME + 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        #'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'NAME': ''
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(ROOT_PROJECT_PATH, 'djangodb.sqlite3'),
    }
}

TEMPLATE_DIRS = (
    BASE_DIR + '/templates/',
    )

if DEBUG or 'test' in sys.argv or 'test_coverage' in sys.argv: #Covers regular testing and django-coverage
    pass
    # DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    # DATABASES['default']['NAME'] = os.path.join(ROOT_PROJECT_PATH, 'db.sqlite3'),
else:
    # Heroku: Parse database configuration from $DATABASE_URL for heroku
    import dj_database_url
    DATABASES['default'] =  dj_database_url.config()


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(ROOT_PROJECT_PATH, 'collected_static_files')


STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    # '/var/www/static/',
)


# This is required for Heroku to prevent "ValueError: dictionary doesn't specify a version"
# I guess heroku default logging settings aren't compatible with Django 1.5
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': [],
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}
# List of modules to import when celery starts.  But crawlnmine/crawlnmine/__init__ should do this already
#CELERY_IMPORTS = ("testcele.tasks",)

# CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
# CELERY_RESULT_BACKEND = "database"
#CELERY_RESULT_DBURI = "mysql://mydb_user:mydb_password@localhost/celery"

# BROKER_URL = 'message_broker://user:password@hostname:port/virtual_host'
# BROKER_URL = 'amqp://new_user:1q2w3e@localhost:5672/myvhost'
# BROKER_URL = 'redis:' #...
