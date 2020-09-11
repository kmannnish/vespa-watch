from django.conf import settings

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import IndividualPicture, NestPicture


def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]


class Command(VespaWatchCommand):
    help = '''Check for unused media files (individual and nest pictures). As a first step, files have a .todelete extension added.'''

    def _get_used_filenames(self):
        models = [IndividualPicture, NestPicture]
        used_filenames_list = []
        for Model in models:
            for entry in Model.objects.all():
                used_filenames_list.append(entry.image.name)

        return frozenset(used_filenames_list)

    def handle(self, *args, **options):
        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
            self.w("S3 is detected")
            import boto3
            s3 = boto3.resource('s3')
            my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
            total_files_counter = 0
            marked_files_counter = 0
            for obj in my_bucket.objects.filter(Prefix='media/pictures'):
                k = obj.key
                self.w(f"Found {k} in bucket, is it something to delete?")
                total_files_counter += 1
                if (k.startswith('media/pictures/individuals') or k.startswith('media/pictures/nests')) and not k.endswith('.todelete'):  # don't delete stuff outside of pictures/individuals and /pictures/nest
                    k_wo_media = remove_prefix(k, 'media/')
                    if k_wo_media not in self._get_used_filenames():
                        self.w(f"Yes, will mark for deletion: {k_wo_media}")

                        # Rename: copy then delete
                        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, f'{k}.todelete').copy_from(CopySource=f'{settings.AWS_STORAGE_BUCKET_NAME}/{k}')
                        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, k).delete()
                        marked_files_counter += 1
                else:
                    self.w(f"Skipping {k}...")
            self.w(f"Done, marked {marked_files_counter}/{total_files_counter} files")
        else:
            self.w("S3 is not used in this environment, skipping.")


