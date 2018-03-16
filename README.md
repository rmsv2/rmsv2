# RMSv2
Rental Management System Version 2 is a software solution for Equipment rental purposes.

Actually the software is under heavy development so we do not recomment to use this software in productive environment.

## Installation

### Requirements
External software requirements are:
* Python3
* Postgres

Python package requirements are:
* django
* django-money
* django-ical
* psycopg2
* Pillow

### Basic installation

1. Clone this repo
2. Switch to repo directory `cd rmsv2`
3. Generate python virtual environment `python3 -m venv venv`
4. Switch to virtual environment `source venv/bin/activate`
5. Install python packages `pip install django django-money django-ical psycopg2 Pillow`
6. Copy default config to configure RMS `cp config/config.default.ini config/config.ini` now edit `config.ini`
7. Execute migrations `python manage.py migrate`
8. Install bower dependencies `cd static` and `bower install`

### Install with apache

If you use apache it is recommended to use the following configuration:

    Alias /rmsv2/static/ /var/www/rmsv2/static/
    
    <Directory /var/www/rmsv2/static/>
            Require all granted
    </Directory>
    
    WSGIDaemonProcess rmswsgi python-home=/var/www/rmsv2 python-path=/var/www/rmsv2
    WSGIProcessGroup rmswsgi
    WSGIScriptAlias /rmsv2 /var/www/rmsv2/rmsv2/wsgi.py process-group=rmswsgi
    <Directory /var/www/rmsv2/rmsv2/>
            <Files wsgi.py>
                    Require all granted
            </Files>
    </Directory>
