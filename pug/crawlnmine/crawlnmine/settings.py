"""
Django settings for crawlnmine project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""


import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# Heroku: Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

PROJECT_SETTINGS_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

# because the apps we want in INSTALLED are "external" to this project (two directories up) we have to add them to the python path manually
ROOT_PROJECT_PATH = os.path.realpath(os.path.join(PROJECT_SETTINGS_PATH,'..','..','..'))

if ROOT_PROJECT_PATH not in sys.path:
    sys.path.insert(1, ROOT_PROJECT_PATH)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5s3an_jk9pd5hc229r1icz1l(_3zt6rhaqr=#(+@b5@&79wzqc'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True


# ALLOWED_HOSTS = []
# Heroku: Allow all hosts
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    #'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django_nvd3',
    # 'celery',

    # 'pug.crawler',
    'pug.miner',
    # 'pug.agile',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'crawlnmine.urls'

WSGI_APPLICATION = 'crawlnmine.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'NAME': ''
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(ROOT_PROJECT_PATH, 'db.sqlite3'),
    }
}


if DEBUG or 'test' in sys.argv or 'test_coverage' in sys.argv: #Covers regular testing and django-coverage
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    DATABASES['default']['NAME'] = os.path.join(ROOT_PROJECT_PATH, 'db.sqlite3'),
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
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(ROOT_PROJECT_PATH, 'collected_static_files')


# List of modules to import when celery starts.  But crawlnmine.crawlnmine.__init__ will do this
#CELERY_IMPORTS = ("testcele.tasks",)

# CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
# CELERY_RESULT_BACKEND = "database"
#CELERY_RESULT_DBURI = "mysql://mydb_user:mydb_password@localhost/celery"

# BROKER_URL = 'message_broker://user:password@hostname:port/virtual_host'
# BROKER_URL = 'amqp://new_user:1q2w3e@localhost:5672/myvhost'
# BROKER_URL = 'redis:' #...
