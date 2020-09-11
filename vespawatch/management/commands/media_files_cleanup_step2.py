from django.conf import settings

from vespawatch.management.commands._utils import VespaWatchCommand


class Command(VespaWatchCommand):
    help = '''Step2: actually delete the files with a ".todelete extensions in media files'''

    def handle(self, *args, **options):
        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
            self.w("S3 is detected")
            import boto3
            s3 = boto3.resource('s3')
            my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

            total_files = 0
            deleted_files = 0
            for obj in my_bucket.objects.filter(Prefix='media/pictures'):
                total_files += 1
                k = obj.key
                if (k.startswith('media/pictures/individuals') or k.startswith(
                    'media/pictures/nests')) and k.endswith('.todelete'):

                    self.w(f"Deleting {k}...")
                    s3.Object(settings.AWS_STORAGE_BUCKET_NAME, k).delete()
                    deleted_files += 1
            self.w(f"Done, deleted {deleted_files}/{total_files} files")