from crawlnmine.settings.common import *

# INSTALLED_APPS += ('storages',)
# AWS_STORAGE_BUCKET_NAME = "pug-webapp"
# STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# S3_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
# STATIC_URL = S3_URL

# DATABASES = {    
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'pugdjangodb',
#         'USER' : 'pugdjangouser',
#         'PASSWORD' : 'pugdjangouserpw',
#         'HOST' : 'pugdjangodb.ctenlqll79ki.us-west-2.rds.amazonaws.com', 
#         'PORT' : '5432',
#     }
# }

print('{} DATABASES:'.format(__file__))
print(DATABASES)