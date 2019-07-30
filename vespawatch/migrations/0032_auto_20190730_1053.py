# Generated by Django 2.1.8 on 2019-07-30 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0031_auto_20190729_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='managementaction',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Comments'),
        ),
        migrations.AddField(
            model_name='managementaction',
            name='number_of_persons',
            field=models.IntegerField(null=True, verbose_name='Number of persons'),
        ),
    ]
