# Generated by Django 3.2.5 on 2022-02-12 16:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('front', '0003_usersymptoms_postcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='user_covid_record',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('covid_record_date', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usersymptoms_date_set', to='front.usersymptoms')),
                ('covid_record_postcode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usersymptoms_postcode', to='front.usersymptoms')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
