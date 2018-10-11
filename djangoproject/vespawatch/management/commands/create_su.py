
import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username=os.environ['VESPA_SU_NAME']).exists():
            User.objects.create_superuser(os.environ['VESPA_SU_NAME'], "admin@admin.com", os.environ['VESPA_SU_PWD'])