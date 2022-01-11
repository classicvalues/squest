# Generated by Django 3.2.9 on 2021-12-23 15:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0007_alter_resource_resource_group'),
        ('profiles', '0003_role_team_teamrolebinding_userrolebinding'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotaAttributeDefinition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('attribute_definitions', models.ManyToManyField(blank=True, help_text='The attribute definitions linked to this quota.', related_name='quota_attribute_definitions', related_query_name='quota_attribute_definitions', to='resource_tracker.ResourceGroupAttributeDefinition', verbose_name='Attribute Definition')),
            ],
        ),
        migrations.CreateModel(
            name='QuotaBinding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('limit', models.FloatField(default=0)),
                ('consumed', models.FloatField(default=0)),
                ('billing_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quota_bindings', to='profiles.billinggroup')),
                ('quota_attribute_definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quota_bindings', to='profiles.quotaattributedefinition')),
            ],
            options={
                'unique_together': {('billing_group', 'quota_attribute_definition')},
            },
        ),
    ]