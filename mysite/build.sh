#!/bin/bash
set -o errexit
# Modify this line as needed for your package manager(pip, poetry,etc)
pip install -r requirement.txt
# Convert static asset files
python manage.py collectstatic --no-input
# apply any outstanding database migrations
python manage.py migrate