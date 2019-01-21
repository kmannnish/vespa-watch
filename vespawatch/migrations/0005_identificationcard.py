# Generated by Django 2.1.2 on 2019-01-21 10:44

from django.db import migrations, models
import django.db.models.deletion
import markdownx.models
import vespawatch.models


class Migration(migrations.Migration):

    dependencies = [
        ('vespawatch', '0004_auto_20190107_1058'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdentificationCard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('represents_nest', models.BooleanField()),
                ('identification_picture', models.ImageField(blank=True, null=True, upload_to=vespawatch.models.IdentificationCard.get_file_path)),
                ('description_nl', markdownx.models.MarkdownxField(blank=True)),
                ('description_en', markdownx.models.MarkdownxField(blank=True)),
                ('order', models.IntegerField(unique=True)),
                ('represented_taxon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='vespawatch.Taxon')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
