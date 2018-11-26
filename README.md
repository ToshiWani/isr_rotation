# ISR Rotation



## Overview

This is a customer support rotation reminder tool. It allows you to:
- Send out reminder email to your team member that who is responsible for customer support today.
- Schedule vacation and holiday
- Update rotation sequence

This web app is:
- Developed by Python 3.6 with Flask 1.02
- Using MongoDB with PyMongo library
- No jQuery 
- All external javascript libraries are referenced via CDN



## Prerequisites 

Use the following two commands to check which version of Python 3 is installed. The python version should be 3.6.x and the location `/usr/bin/python3`

```bash
$ python3 --version
$ which python3
```

Install following packages after upgrading

```bash
$ sudo apt update && sudo apt upgrade
$ sudo apt install python3-dev python3-pip python3-virtualenv
```

Install Apache server if it is not installed yet.

```bash
$ sudo apt install apache2 apache2-dev
```


Check if system timezone is local (America/New_York).  If it is UTC, you may want to change it to local time where most users are located.  Otherwise, vacation and holiday schedules may not be sync as expected.
```bash
# Check current timezone

$ timedatectl
                      Local time: Mon 2018-11-26 01:21:39 UTC
                  Universal time: Mon 2018-11-26 01:21:39 UTC
                        RTC time: Mon 2018-11-26 01:21:40
                       Time zone: Etc/UTC (UTC, +0000)
       System clock synchronized: yes
systemd-timesyncd.service active: yes
                 RTC in local TZ: no


# Update system timezone to the local timezone (America/New_York)

$ sudo timedatectl set-timezone America/New_York

# Reboot the machine

$ sudo reboot
```

## Clone from git

Clone this quickstart project under Apache's document directory `/var/www`. And, give permission to `www-data`
```bash
$ git clone https://github.com/ToshiWani/isr_rotation.git /var/www/isr_rotation
$ sudo chown -R www-data:www-data /var/www/isr_rotation/
$ sudo chmod -R 775 /var/www/isr_rotation/
```

Copy `config.py.example.py` and rename it `config.py`.  Update config file for your own environment.
```bash
$ cp /var/www/isr_rotation/isr_rotation/config.py.example.py /var/www/isr_rotation/isr_rotation/config.py
$ vim /var/www/isr_rotation/isr_rotation/config.py
```


## Virtual Environment

Upgrade pip and setuptools to the latest version, if you haven't done it yet.

```bash
$ pip3 install --upgrade pip setuptools
```

Create a shared venv location in a user-neutral directory, and make it group-readable

```bash
$ sudo mkdir /usr/local/share/venvs
$ sudo chown -R www-data:www-data /usr/local/share/venvs/
$ sudo chmod -R 775 /usr/local/share/venvs/
```

Create virtual environment

```bash
$ python3.6 -m venv /usr/local/share/venvs/isr_rotation_venv
```

Active the virtualenv

```bash
$ source /usr/local/share/venvs/isr_rotation_venv/bin/activate
```

At this point, virtual environment should be activated.  Your SSH terminal should looks like this:

```bash
(isr_rotation_venv) username@yourmachine:~$ 
```


## Setup apache server

To run Flask on Apache server, we need to install a gateway interface called WSGI (Web Server Gateway Interface)

```bash
$ pip3.6 install mod_wsgi
```

Next, we need to linkup the shared object file and home directory of WSGI.

```bash
$ mod_wsgi-express module-config

LoadModule wsgi_module "/usr/local/share/venvs/isr_rotation_venv/lib/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so"
WSGIPythonHome "/usr/local/share/venvs/isr_rotation_venv"
```

Open the `wsgi.load` file and replace the contents with the two lines of codes generated the previous step. (You may want to keep the backup of the file before overwrite it.)
```bash
$ sudo cp /etc/apache2/mods-available/wsgi.load /etc/apache2/mods-available/wsgi.load.bak
$ sudo vim /etc/apache2/mods-available/wsgi.load
```

Enable updated WSGI and restart Apache server
```bash
$ sudo a2enmod wsgi
$ sudo service apache2 restart
```



## Update VirtualHost

Restore packages from `requirements.txt`

```bash
$ pip3.6 install -r /var/www/isr_rotation/requirements.txt
```

Create a new virtual host file `flask_quickstart.conf` 
```bash
$ sudo vim /etc/apache2/sites-available/flask_quickstart.conf
``` 

Paste the content below. Replace the `ServerName` parameter for your own server IP address. If it is not sure, use the IP address of the `inet` by running the `ifconfig` command.  Please note that the `isr_rotation` directory is under another `isr_rotation`. This is not an error.  Also make sure that the `isr_rotation.wsgi` file is under the first `isr_rotation` directory.
```xml
<VirtualHost *:80>
     ServerName xxx.xxx.xxx.xxx
     ServerAdmin your@email.com
     WSGIScriptAlias / /var/www/isr_rotation/isr_rotation.wsgi
     <Directory /var/www/isr_rotation/isr_rotation/>
        Order allow,deny
        Allow from all
     </Directory>
     ErrorLog ${APACHE_LOG_DIR}/isr_rotation-error.log
     LogLevel warn
     CustomLog ${APACHE_LOG_DIR}/isr_rotation-access.log combined
</VirtualHost>
```

So far, your Apache document `/var/www/isr_rotation` directory would look like this...

```
isr_rotation
├── isr_rotation
│   ├── authentication.py
│   ├── blueprints
│   ├── caching.py
│   ├── config.py
│   ├── config.py.example.py
│   ├── database.py
│   ├── __init__.py
│   ├── mailer.py
│   ├── static
│   └── user.py
├── isr_rotation.wsgi
├── README.md
└── ...

```


Activate the virtual host and restart Apache

```bash
$ sudo a2ensite flask_quickstart.conf
$ sudo service apache2 restart
```



## Setup crontab (scheduled job)


To send notification email every morning, you can update crontab to execute the shell script file `move_next.sh`. First, open the `crontab` with an text editor.

```bash
$ sudo vim /etv/crontab
```

Add a new job to it. Below is example to execute `move_next.sh` at 2 AM only weekdays. (Note: if system timezone of your machine is set to UTC, use UTC time here.)

```bash
0  2    * * 1-5 root    /var/www/isr_rotation/move_next.sh
```
