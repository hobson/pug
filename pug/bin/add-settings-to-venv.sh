# get rid of dependency on manage.py and any DJANGO_SETTINGS_MODULE env var being set in scripts
if [ -n $1 ]; then
    cd $1
    add2virtualenv .
    echo "export DJANGO_SETTINGS_MODULE=$1.settings" >> $VIRTUAL_ENV/bin/postactivate
    echo "unset DJANGO_SETTINGS_MODULE" >> $VIRTUAL_ENV/bin/postdeactivate
    deactivate
    workon $1
    # rm manage.py
    django-admin.py runserver
fi