from django.conf import settings

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import IndividualPicture, NestPicture


def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]


class Command(VespaWatchCommand):
    help = '''Check for unused media files (individual and nest pictures). As a first step, files have a .todelete extension added.'''

    def handle(self, *args, **options):
        models = [IndividualPicture, NestPicture]
        used_filenames_list = []
        for Model in models:
            self.w(f"Will cleanup pictures linked to {Model}")
            for entry in Model.objects.all():
                used_filenames_list.append(entry.image.name)

        # 1. Get the list of used filenames in the app
        used_filenames = frozenset(used_filenames_list)

        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
            self.w("S3 is detected")
            import boto3
            s3 = boto3.resource('s3')
            my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
            for obj in my_bucket.objects.filter(Prefix='media/pictures'):
                k = obj.key
                if k.startswith('media/pictures/individuals') or k.startswith('media/pictures/nests'):  # don't delete stuff outside of pictures/individuals and /pictures/nest
                    k_wo_media = remove_prefix(k, 'media/')
                    if k_wo_media not in used_filenames:
                        self.w(f"Will mark for deletion: {k_wo_media}")

                        # Rename: copy then delete
                        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f'{k}.todelete').copy_from(CopySource=f'{settings.AWS_STORAGE_BUCKET_NAME}/{k}')
                        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, k).delete()
                    else:
                        self.w(f"{k_wo_media} is in use, skipping....")
                else:
                    self.w(f"Skipping {k}...")
        else:
            self.w("S3 is not used in this environment, skipping.")


