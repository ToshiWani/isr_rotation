# ISR Rotation



## Overview

This is a customer support rotation reminder tool. It allows you to:
- Send out reminder email to your team member that who is responsible for customer support today.
- Schedule vacation and holiday
- Update rotation sequence

This web app is:
- Developed by python with Flask framework
- Using SQLAlchemy as ORM.


## Setup Virtual Environment

- Install virtual environment
    ```bash
    $ sudo apt-get install python-virtualenv
    ```

- Crate a virtual environment named "venv" and switch to the virtual environment
    ```bash
    $ virtualenv venv
    $ . venv/bin/activate

    ```
    
- As a side note, if you want get our from virtual environment, run the command
    ```bash
    $ deactivate
    ```

- Install libraries, like Flask, SQLAlchemy
    ```bash
    $ pip install -r requirements.txt
    ```
- As a side node, this is how you can find the full path of libraries
    ```bash
    $ pip show -f <package name>
    ```
- Install wsgi
    ```bash
    $ apt-get install libapache2-mod-wsgi
    ```
- Make sure the adapter.wsgi file is pointing to the correct paths
    Example:
    ```
    activate_this = '/var/www/html/rotation/venv/bin/activate_this.py'
    sys.path.insert(0, '/var/www/html/rotation')
    ```


## Restore Files and Libraries


### Config File

- Copy config.py.exmple and rename it to config.py
- Update DATABASE_URI, which must be a full path.
- Go to www.mailjet.com and get API public key and secret key
    Example:
    ```python
    DATABASE_URI = 'sqlite:////var/www/html/isr_rotation/isr_rotation.db'
    LOG_LEVEL = 'INFO'
    EMAIL_API_KEY = 'xxxxxx'
    EMAIL_API_SECRET = 'xxxxxx'
    ```

### Packages

- Install Javascript dependencies
    ```bash
    $ cd isr_rotation/static/
    $ npm install
    ```

### Initialize Database
To initialize database, run following python scripts:
```python
>>> from isr_request.database from init_db
>>> init_db()
```


## Server Configurations

### Apache

- Create a new file in /etc/apache2/sites-available and add/edit parameters.
    ```
    DocumentRoot /var/www/html/isr_rotation
    WSGIDaemonProcess isr_rotation user=xxxxxxx group=adm threads=5
    WSGIScriptAlias / /var/www/html/isr_rotation/adapter.wsgi
    <Directory /var/www/html/rotation>
    	WSGIProcessGroup isr_rotation
    	WSGIApplicationGroup %{GLOBAL}
    	Order deny,allow
    	Allow from all
    </Directory>
    ```
- Disable current site-available and enable a new
    ```bash
    $ a2dissite <filename>
    $ a2ensite <filename>
    ```

### Cron

Schedule cron to run sendmail.sh one a day. The script just executes mailsender.py.

