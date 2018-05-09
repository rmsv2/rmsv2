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
* PyPDF2
* reportlab
* typing

### Basic installation

1. Clone this repo
2. Switch to repo directory `cd rmsv2`
3. Generate python virtual environment `python3 -m venv venv`
4. Switch to virtual environment `source venv/bin/activate`
5. Install python packages `pip install django django-money django-ical psycopg2 Pillow PyPDF2 reportlab typing`
6. Copy default config to configure RMS `cp config/config.default.ini config/config.ini` now edit `config.ini`
7. Execute migrations `python manage.py migrate`
8. Install bower dependencies `cd static` and `bower install`
9. add initial admin user `python3 manage.py createsuperuser`

#### Install with apache

If you use apache it is recommended to use the following configuration:

    Alias /rmsv2/static/ /var/www/rmsv2/static/
    
    <Directory /var/www/rmsv2/static/>
            Require all granted
    </Directory>
    
    WSGIDaemonProcess rmswsgi python-home=/var/www/rmsv2 python-path=/var/www/rmsv2
    WSGIProcessGroup rmswsgi
    WSGIScriptAlias /rmsv2 /var/www/rmsv2/rmsv2/wsgi.py process-group=rmswsgi
    WSGIPassAuthorization On
    
    RewriteEngine on
    RewriteCond %{HTTP:Authorization} ^(.*)
    RewriteRule .* - [e=HTTP_AUTHORIZATION:%1]
    
    <Directory /var/www/rmsv2/rmsv2/>
            <Files wsgi.py>
                    Require all granted
            </Files>
    </Directory>

#### Install with nginx and uwsgi

First you need to install `uwsgi` inside the virtual environment

    pip install uwsgi

To install `uwsgi` you first need to install a C compiler like gcc.

Now we need to configure nginx.
Create the file `/etc/nginx/sites-available/rmsv2` with the following content:

    server {
        listen 80;
        
        charset utf-8;
        
        location /static {
            alias /var/www/rmsv2/static;
        }
        
        location / {
            uwsgi_pass unix:///var/run/rmsv2.socket;
            include uwsgi_params;
        }
    }

Now you can run `uwsgi` manually from inside the virtual environment

    uwsgi --uwsgi-socket /tmp/rmsv2.socket --module rmsv2.wsgi --uid 33 --gid 33 --thunder-lock

and all things working well.

But of course it's better to run this in a service, so here is a sample systemd service file

    [Unit]
    Description=uWSGI serve for rmsv2 system
    
    [Service]
    ExecProStart=source venv/bin/sctivate
    ExecStart=uwsgi --uwsgi-socket /tmp/rmsv2.socket --module rmsv2.wsgi
    WorkingDirectory=/var/www/rmsv2/
    User=www-data
    Group=www-data
    
    [Install]
    WantedBy=multi-user.target

copy this to the file `/etc/systemd/system/rms_uwsgi.service` and execute the following to enable and start the service.

    systemctl daemon-reload
    systemctl enable rms_uwsgi.service
    systemctl start rms_uwsgi.service
