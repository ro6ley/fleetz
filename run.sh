#!/bin/sh
# run migrations
python manage.py migrate

# add cron job to run every hour
echo "0 * * * * /usr/local/bin/python /fleetz/manage.py runcrons --force" >> /etc/crontabs/root

# start cron
crond

# start job to process tasks
nohup python manage.py process_tasks &

# start django
python manage.py runserver 0.0.0.0:80
