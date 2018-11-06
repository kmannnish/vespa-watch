from django.core.management import BaseCommand


class VespaWatchCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(VespaWatchCommand, self).__init__(*args, **kwargs)

        self.w = self.stdout.write  # Alias to save keystrokes :)