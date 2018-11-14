from django.contrib.auth.models import User
from django.utils.text import slugify

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import FirefightersZone
from vespawatch.utils import make_password


class Command(VespaWatchCommand):
    help = 'Create a user account for each firefighters zone in the database, and output the credentials.'

    def handle(self, *args, **options):
        self.w("Creating a user account for each zone...")
        for zone in FirefightersZone.objects.all():
            username = slugify(zone.name)
            password = make_password()

            user = User.objects.create_user(username=username,
                                            password=password)
            user.profile.zone = zone
            user.save()

            self.w(f"Created {username} / {password} (for {zone.name})")

        self.w("OK")