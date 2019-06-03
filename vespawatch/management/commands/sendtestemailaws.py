import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from vespawatch.management.commands._utils import VespaWatchCommand


class Command(VespaWatchCommand):
    help = 'Send a email with AWS SES to see if our configuration is ok'
    email_client = None

    def send_email_to_reporter(self, inat_id, recipient_email):
        if not self.email_client:
            self.w('set up email client')
            self.email_client = boto3.client('ses', region_name=settings.AWS_S3_REGION_NAME)

        self.w('sending email')
        body = settings.EMAIL_TEMPLATE.format(
            title='Vespawatch email',
            message='Beste, bedankt voor uw waarneming. Deze werd nu gepubliceerd op iNaturalist met id {}'.format(inat_id)
        )
        subject = 'Thank you for your Vespawatch observation'
        try:
            # Provide the contents of the email.
            response = self.email_client.send_email(
                Destination={
                    'ToAddresses': [
                        recipient_email,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': settings.EMAIL_CHARSET,
                            'Data': body,
                        },
                    },
                    'Subject': {
                        'Charset': settings.EMAIL_CHARSET,
                        'Data': subject,
                    },
                },
                Source=settings.EMAIL_SENDER,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            self.w(e.response['Error']['Message'])
        else:
            self.w("Email sent! Message ID:"),
            self.w(response['MessageId'])

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='the recipient to send the email address to')

    def handle(self, *args, **options):
        self.send_email_to_reporter('someinatID', options['recipient'])
