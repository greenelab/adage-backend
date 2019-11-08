#!/bin/bash
#
# This script should be run by a user who has "sudo" privilege
# (such as "ubuntu" on AWS EC2).

# Install Nginx and Supervisor
sudo apt-get update && apt-get upgrade -y
sudo apt-get install python3 nginx supervisor -y

# Install certbot for SSL certificate in HTTPS
sudo add-apt-repository ppa:certbot/certbot --yes
sudo apt update
sudo apt install certbot python-certbot-nginx -y

# Certbot config
# Fill "<email>" and "<domain_name>" into the following command:
# sudo certbot --nginx -n -m <email> --no-eff-email certonly -d <domain_name> --agree-tos

# "pg_config" command in libpq-dev is required to compile "psycopg2",
# which is included in "py3-adage-backend/adage/requirements.txt"
sudo apt-get install libpq-dev

# Create venv
mkdir $HOME/.venv
python3 -m venv $HOME/.venv/adage
source $HOME/.venv/adage/bin/activate

# Clone code and install PyPI packages
cd && git clone https://github.com/greenelab/py3-adage-backend.git

# Optional: "git checkout <br_name>" for test
# ... ...

# Upgrade pip, then install all required PyPI packages
pip install pip --upgrade
pip install -r $HOME/py3-adage-backend/adage/requirements.txt

# Create "secrets.yml" in $HOME/py3-adage-backend/adage/adage/
# ... ...
# PostgreSQL specific: log into the database "template1" and run
# this psql command: "CREATE EXTENSION IF NOT EXISTS pg_trgm"

# Create static directory and have it populated so that the Django REST
# Framework API view can be rendered correctly.
mkdir -p $HOME/www/static
$HOME/py3-adage-backend/adage/manage.py collectstatic

# Nginx config
sudo rm -f /etc/nginx/sites-enabled/default
sudo cp $HOME/py3-adage-backend/deployment/nginx.conf /etc/nginx/sites-available/adage.conf
cd /etc/nginx/sites-enabled/
sudo ln -s ../sites-available/adage.conf .

# Supervisor config
sudo cp $HOME/py3-adage-backend/deployment/supervisor-adage.conf /etc/supervisor/conf.d/adage-gunicorn.conf
# create log file
sudo touch /var/log/adage-gunicorn.log
# Make "ubuntu" the owner of the log file
sudo chown nobody:nogroup /var/log/adage-gunicorn.log

# Restart Supervisor and Nginx
sudo systemctl restart supervisor
sudo systemctl restart nginx
