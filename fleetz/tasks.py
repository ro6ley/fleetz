from django.conf import settings
from django_cron import CronJobBase, Schedule

from .models import FleetzUser


class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 60 * settings.CRON_JOBS_INTERVALS_IN_HOURS

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'fleetz.web.cron_job'

    def do(self):
        """ This method will be used by the cronjob to fetch the last 25 tweets 
        posted by all users periodically.
        """
        fleetz_users = FleetzUser.objects.all()
        for user in fleetz_users:
            user.fetch_and_schedule_tweets()
