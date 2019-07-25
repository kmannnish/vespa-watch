from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import IndividualPicture, NestPicture


class Command(VespaWatchCommand):
    help = '''Images are created when they are uploaded with the dropzone. This can create orphan images (images that
    are not attached to an observation). This command can be used to remove these'''

    def handle(self, *args, **options):
        for obj in list(IndividualPicture.objects.filter(observation__isnull=True).all()) + list(NestPicture.objects.filter(observation__isnull=True).all()):
            self.w(f'Delete picture: {obj}')
            obj.delete()
