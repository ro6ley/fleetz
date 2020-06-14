<p align="center">
    <a href="#"><img src="https://github.com/ro6ley/fleetz/workflows/AWS%20Deployment/badge.svg" alt="AWS Deployment"></a>
    <a href="http://hits.dwyl.com/ro6ley/fleetz"><img src="http://hits.dwyl.com/ro6ley/fleetz.svg" alt="Hits"></a>
    <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="MIT License"></a>
    <a href="https://github.com/ellerbrock/open-source-badge/"><img src="https://badges.frapsoft.com/os/v1/open-source.png?v=103" alt="Open Source Love"></a>
</p>

<p align="center">
  <h1>FLEETZ .:!:.</h1>
</p>

Fleetz is a bot that makes tweets disappear after 24 hours (-ish) just like stories on other platforms.

---

It periodically fetches your tweets in batches and checks for any trigger characters at the end of the tweet. These triggers are the last character of a tweet and can be any character or emoji, apart from a `pipe character (|)`.

Unlike other platforms, Fleetz allows you to configure how long a posted "Fleet" stays up. By default, the bot will delete any tweets having any of the triggers after 24 hours and 24 minutes. This duration is configurable in the profile page.

On the same page, you also be able to see any tweets that are scheduled for deletion, when they will be deleted, and you can unschedule a Tweet to avoid it's deletion.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Building Blocks

This is the tech stack needed to run Fleetz:

* [Python 3.8](https://www.python.org/downloads/)
* [Bootstrap v4](https://getbootstrap.com) - The HTML framework.
* [Moment.js](https://momentjs.com) - For timezones.
* [Django 2.2 LTS](https://www.djangoproject.com/) - The web framework.
* [PostgreSQL](https://www.postgresql.org/) - The database (**REQUIRED**).
* [Docker](https://www.docker.com/get-started) (Optional)
* [Dokku](http://dokku.viewdocs.io/dokku~v0.20.4/getting-started/installation/) (Optional)

> NOTE: PostgreSQL is required as Fleetz uses ArrayFields which only work on PostgreSQL. If you intend to use another database, make sure you modify the field in [models](fleetz/models.py), and the field in [forms](fleetz/forms.py).

### Environment variables

The following environment variables are needed to be set when running the project or Docker image:

* `DB_NAME` - Name of the database
* `DB_HOST` - Location of the database
* `DB_PORT` - Database port
* `DB_USER` - Username used to access the database
* `DB_PASSWORD` - Password used to access the database
* `CONSUMER_API_KEY` (optional) - as provided by Twitter on the developer portal, configuring a Twitter App as a Social App will provide it
* `CONSUMER_API_SECRET_KEY` (optional) - as provided by Twitter on the developer portal, configuring a Twitter App as a Social App will provide it
* `DJANGO_DEBUG` - see [Django Docs: Debug](https://docs.djangoproject.com/en/3.0/ref/settings/#debug)
* `DJANGO_SECRET_KEY` - see [Django Docs: Secret Key](https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key)

### Local Development

* clone the repo:

    ```
    $ git clone https://github.com/ro6ley/fleetz.git
    $ cd fleetz
    ```

* create and activate a virtualenv and install dependencies:

    ```
    $ virtualenv env --no-site-packages
    $ source env/bin/activate
    $ pip -r requirements.txt'
    ```

* create a postgresql user with username and password `fleetz` and create a corresponding database called `fleetz_dev`.

    ```
    $ sudo su - postgres -c 'createuser -d -P fleetz'
    $ sudo su - postgres -c 'createdb fleetz_dev'
    ```

* check that you can connect to the postgresql database as your regular shell user (not indigo user) by means of password authentication:

    ```
    $ psql -h localhost fleetz_dev fleetz
    ```

    > If you can't connect, you can modify your `pg_hba.conf` (`/etc/postgresql/9.6/main/pg_hba.conf` for postgresql 9.6) to allow md5 encrypted password authentication for users on localhost by adding a line like this:
    > ```
    > local	all		all     md5
    > ```

* run migrations to setup the initial database:
    ```
    $ python manage.py migrate
    ```

* create the superuser:

    ```bash
    $ python manage.py createsuperuser
    ```

* start the server:

    ```bash
    $ python manage.py runserver
    ```

* Set up the Twitter integration by by going to [http://localhost:8000/admin](http://localhost:8000/admin), choosing **Social applications** under **Social Account** and clicking **Add Social Application** and filling in the required app details as provided by Twitter.

* set up the cron job to sync tweets:
    ```
    $ python manage.py crontab add
    ```

* confirm cronjob have been set up:
    ```
    $ crontab -l
    ```

* run background tasks to delete tweets as scheduled:
    ```
    $ python manage.py process_tasks
    ```
    > This will simply poll the database queue every few seconds to see if there is a new task to run.

* navigate to [http://localhost:8000](http://localhost:8000/) and click on sign up to proceed.

### Running in Docker

* build the Docker image
    ```
    $ docker build -t fleetz:v1 .
    ```

* run the docker image while passing your Google Analytics ID as an environment variable:
    ```
    $ docker run -it -p 80:8000 -e CONSUMER_API_KEY='your_twitter_api_key' CONSUMER_API_SECRET_KEY='you_twitter_consumer_key_secret' --name fleetz fleetz:v1
    ```

* find the name or ID of the container by running:
    ```
    $ docker ps
    CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
    2e0e019f74ad        fleetz:v1           "python manage.py ru…"   9 minutes ago       Up 9 minutes        0.0.0.0:80->8000/tcp   loving_grothendieck
    ```

* use the name to access the container:
    ```
    $ docker exec -it fleetz /bin/sh
    /fleetz #
    ```

* create a superuser (_first time only_):
    ```
    $ python manage.py createsuperuser
    ```

* navigate to http://127.0.0.1:8000/admin and add your Twitter App credentials 
  as obtained from the [Twitter Dev](https://developer.twitter.com/en/apps) page by creating a new
  SocialApp (_first time only_).

* you and your users can now sign in via Twitter and use the bot 🥳

### Production deployment

Changes to the master branch are automatically deployed using [GitHub Actions](https://github.com/ro6ley/fleetz/actions) to AWS. The
workflow is described in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

Requires the following additional dokku plugins:

* Install [dokku deployment-keys plugin](https://github.com/cedricziel/dokku-deployment-keys) and add the deployment user's public and private key to `~dokku/.deployment-keys/shared/.ssh/`
* Install [dokku hostkeys plugin](https://github.com/cedricziel/dokku-hostkeys-plugin) and add the github.com keys: `dokku hostkeys:shared:autoadd github.com` -- you may need to run this 3 or 4 times to get all the github hosts.

## Authors

* **[Robley Gori](https://github.com/ro6ley)** - *Initial work*

See also the list of [contributors](https://github.com/ro6ley/fleetz/contributors) who participated in this project.

## License

This project is licensed under the GNU General Public License v3.0.

### Resources

#### Dokku deployment
- https://github.com/dokku/dokku/issues/1860#issuecomment-188123117
- http://craigbeck.io/2016/01/13/dokku-plus-dockerfile-deployments/
- https://www.stavros.io/posts/deploy-django-dokku/
- https://www.accordbox.com/blog/how-deploy-django-project-dokku-docker/
- https://github.com/dokku/dokku/issues/1878
