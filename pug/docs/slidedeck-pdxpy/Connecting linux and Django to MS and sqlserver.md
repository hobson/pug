Connecting Django (on centos/fedora/redhat) to a mssqlserver 

-----

Download and install ["Microsoft SQL Server 2012 Express"](http://www.microsoft.com/en-us/download/details.aspx?id=29062)

-----

If your python world isn't in order, pip and virtualenv can help

    #!/usr/bin/env bash
    deactivate 2>/dev/null
    sudo yum remove python-pip python-virtualenv
    sudo yum install --updated -y python python-setuptools python-devel libxml2 libxml2-devel zlib-devel openssl-devel curl
    mkdir -P ~/src/pip
    cd ~/src/pip
    curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    sudo python get-pip.py
    sudo pip install virtualenvwrapper

-----

Install TDS and ODBC for linux 

    #!/usr/bin/env bash
    sudo yum install --updated -y pcre pcre-devel gcc make autoconf automake unixODBC* freetds*

-----

Backup and edit `/etc/odbcinst.ini`

    #!/usr/bin/env bash
    sudo cp /etc/odbcinst.ini /etc/odbcinst.ini.bak
    echo '
    [FreeTDS]
    Description=TDS driver (Sybase / MS SQL)
    Driver=/usr/lib64/libtdsodbc.so
    Setup=/usr/lib64/libtdS.so
    FileUsage=1
    ' >> /etc/odbcinst.ini

6. Add the DB to your Django settings.DATABASES

    #!/usr/bin/env python
    DATABASES = {
        'default': {
           'ENGINE': 'sql_server.pyodbc'  
            'NAME': 'mydatabasename',                 
            'USER': 'yourusername',
            'PASSWORD': 'yourpassword',
            'HOST': '192.168.1.127',
            # 'HOST': 'fully.qualified.domain.nm',
            'PORT': '1433',  
            'OPTIONS':{  'host_is_server': True,    }                
        },
    }

7. Connect to the database

Using Django:

    ~~~~~~~~~~~~~~~~~~~~~~~
    #!/usr/bin/env python
    from django.db import connections
    conn = connections['default']
    print conn.introspection.table_names(conn.cursor())
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

With pyodbc:

    #!/usr/bin/env python
    from django.conf import settings
    import pyodbc
    connection_string = "Driver=FreeTDS;Server=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=7.2;PORT=%s" % (
        settings.DATABASES['default']['HOST'], 
        settings.DATABASES['default']['NAME'],
        settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['PASSWORD'],
        settings.DATABASES['default']['PORT'],
        )
    print conn.introspection.table_names(conn.cursor())




