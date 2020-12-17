#!/bin/bash
#
# This script should be run by a user who has "sudo" privilege
# (such as "ubuntu" on AWS EC2 or Compute Engine of Google Coud Platform).

# Optional: set timezone to US East
sudo timedatectl set-timezone America/New_York

# Package update
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y emacs tree

# PostgreSQL client, which includes commands such as `psql`, `pg_dump`,
# `createuser`, `createdb`, `dropuser`, `dropdb`, etc.
sudo apt-get install -y postgresql-client

# Compiler and libraries to compile Python 3.X packages
sudo apt-get install gcc python3-dev

# `pg_config` command in libpq-dev is required to compile "psycopg2",
# which is included in "adage-backend/adage/requirements.txt"
sudo apt-get install libpq-dev

# "venv" module in Python 3.X
sudo apt-get install -y python3-venv

# Create venv
mkdir $HOME/.venv
python3 -m venv $HOME/.venv/adage
source $HOME/.venv/adage/bin/activate

# Clone code and install PyPI packages
cd && git clone https://github.com/greenelab/adage-backend.git

# Upgrade pip, then install all required PyPI packages
pip install pip --upgrade
pip install -r $HOME/adage-backend/adage/requirements.txt

##############################################################
#    Create pickled file for "unpickled genesets" query
##############################################################
# Query endpoint:
# https:<host>/api/v1/tribe_client/return_unpickled_genesets?organism=Pseudomonas+aeruginosa&model=1
cd $HOME/adage-backend/deployment
python3 ./create_pickled_genesets.py

# Create static directory and have it populated so that the Django REST
# Framework API view can be rendered correctly.
mkdir -p $HOME/www/api/static
$HOME/py3-adage-backend/adage/manage.py collectstatic

##############################################################
#             Nginx & Certbot
##############################################################
# Install packages
sudo apt-get install -y nginx
sudo apt-get install -y certbot python3-certbot-nginx

# Install SSL certificate
EMAIL="team@greenelab.com"
DOMAIN_NAME="api-adage.greenelab.com"
sudo certbot certonly \
     --nginx \
     --noninteractive --no-eff-email --agree-tos \
     --email $EMAIL \
     --domains ${DOMAIN_NAME}

# Copy nginx config file
sudo rm -f /etc/nginx/sites-enabled/default
sudo cp $HOME/adage-backend/deployment/nginx.conf /etc/nginx/sites-available/adage.conf
cd /etc/nginx/sites-enabled/
sudo ln -s ../sites-available/adage.conf .

##############################################################
#      Install supervisor to manage gunicorn
##############################################################
# Install package
sudo apt-get install -y supervisor

# Copy supervisor config file
sudo cp $HOME/adage-backend/deployment/supervisor-adage.conf /etc/supervisor/conf.d/adage-gunicorn.conf

# Create gunicorn log file and set its ownership
sudo touch /var/log/supervisor/adage-gunicorn.log
sudo chown nobody:nogroup /var/log/supervisor/adage-gunicorn.log

# Restart Supervisor and Nginx
sudo systemctl restart supervisor
sudo systemctl restart nginx

# Reminder: "$HOME/adage-backend/adage/adage/config.yml" must exist
if [ ! -e $HOME/adage-backend/adage/adage/xxconfig.yml ]; then
    echo "Reminder: config.yml not found in $HOME/adage-backend/adage/adage/"
    echo "Please create it and restart the app by 'systemctl restart supervisor' command"
    exit 1
fi
