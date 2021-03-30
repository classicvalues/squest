# Generated by Django 3.1.7 on 2021-03-30 13:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_fsm


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('django_celery_beat', '0015_edit_solarschedule_events_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('spec', models.JSONField(default=dict)),
                ('state', django_fsm.FSMField(default='PENDING', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='JobTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('tower_id', models.IntegerField()),
                ('survey', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('type', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete')], default='CREATE', max_length=10)),
                ('enabled_survey_fields', models.JSONField(default=dict)),
                ('auto_accept', models.BooleanField(default=False)),
                ('auto_process', models.BooleanField(default=False)),
                ('process_timeout_second', models.IntegerField(default=60)),
                ('job_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.jobtemplate')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('image', models.ImageField(blank=True, upload_to='service_image')),
            ],
        ),
        migrations.CreateModel(
            name='TowerServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('host', models.CharField(max_length=200, unique=True)),
                ('token', models.CharField(max_length=200)),
                ('secure', models.BooleanField(default=True)),
                ('ssl_verify', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fill_in_survey', models.JSONField(default=dict)),
                ('date_submitted', models.DateField(auto_now=True, null=True)),
                ('date_complete', models.DateField(blank=True, null=True)),
                ('tower_job_id', models.IntegerField(blank=True, null=True)),
                ('state', django_fsm.FSMField(choices=[('SUBMITTED', 'SUBMITTED'), ('NEED_INFO', 'NEED_INFO'), ('REJECTED', 'REJECTED'), ('ACCEPTED', 'ACCEPTED'), ('CANCELED', 'CANCELED'), ('PROCESSING', 'PROCESSING'), ('COMPLETE', 'COMPLETE'), ('FAILED', 'FAILED')], default='SUBMITTED', max_length=50)),
                ('periodic_task_date_expire', models.DateTimeField(blank=True, null=True)),
                ('failure_message', models.TextField(blank=True, null=True)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.instance')),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.operation')),
                ('periodic_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_beat.periodictask')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='operation',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.service'),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_message', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='service_catalog.request')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='tower_server',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.towerserver'),
        ),
        migrations.AddField(
            model_name='instance',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='service_catalog.service'),
        ),
        migrations.CreateModel(
            name='UserPermissionOnInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service_catalog.instance')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_permission_on_instance',
                'unique_together': {('instance', 'user')},
            },
        ),
    ]
