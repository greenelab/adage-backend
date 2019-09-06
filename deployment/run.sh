#!/bin/bash
#
# Assume this script is run by a regular user (such as "ubuntu" on AWS EC2).

# Install Nginx and Supervisor
sudo apt-get update && apt-get upgrade -y
sudo apt-get install python3 nginx supervisor -y

# "pg_config" command in libpq-dev is required to compile "psycopg2",
# which is included in "py3-adage-backend/adage/requirements.txt"
sudo apt-get install libpq-dev

# Create venv
mkdir ~/.venv
python3 -m venv ~/.venv/adage
source ~/.venv/adage/bin/activate

# Clone code and install PyPI packages
cd && git clone https://github.com/greenelab/py3-adage-backend.git

# Optional: "git checkout <br_name>" for test
# ... ...

# Upgrade pip, then install all required PyPI packages
pip install pip --upgrade
pip install -r ~/py3-adage-backend/adage/requirements.txt

# Create "secrets.yml" in ~/py3-adage-backend/adage/adage/
# ... ...

# Create static directory and have it populated so that the Django REST
# Framework API view can be rendered correctly.
mkdir -p ~/www/static
~/py3-adage-backend/adage/manage.py collectstatic

# Create Nginx and Supervisor config files
# ... ...

# Restart Supervisor and Nginx
sudo systemctl restart supervisor
sudo systemctl restart nginx
