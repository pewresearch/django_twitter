# Generated by Django 3.1.2 on 2020-11-25 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0007_auto_20201015_0833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaltweet',
            name='text',
            field=models.CharField(max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='text',
            field=models.CharField(max_length=1500, null=True),
        ),
    ]