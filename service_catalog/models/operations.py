import copy

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


from service_catalog.models import JobTemplate, OperationType
from service_catalog.models import Service


class Operation(models.Model):
    name = models.CharField(max_length=100, verbose_name="Operation name")
    description = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(
        max_length=10,
        choices=OperationType.choices,
        default=OperationType.CREATE,
        verbose_name="Operation type"
    )
    enabled_survey_fields = models.JSONField(default=dict)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="operations",
                                related_query_name="operation")
    job_template = models.ForeignKey(JobTemplate, null=True, on_delete=models.SET_NULL)
    auto_accept = models.BooleanField(default=False)
    auto_process = models.BooleanField(default=False)
    process_timeout_second = models.IntegerField(default=60, verbose_name="Process timeout (s)")

    def clean(self):
        if hasattr(self, 'service'):
            if self.type == OperationType.CREATE:
                if self.service:
                    if self.service.operations.filter(type=OperationType.CREATE).count() != 0:
                        if self.service.operations.filter(type=OperationType.CREATE).first().id != self.id:
                            raise ValidationError({'service': _("A service can have only one 'CREATE' operation")})

    def update_survey(self, save=True):
        new_end_user_survey = dict()
        old_enabled_survey_fields = copy.copy(self.enabled_survey_fields)
        if self.job_template is not None:
            for survey_field in self.job_template.survey.get("spec", []):
                field_id = survey_field["variable"]
                if field_id not in old_enabled_survey_fields:
                    new_end_user_survey[field_id] = True
                else:
                    new_end_user_survey[field_id] = old_enabled_survey_fields[field_id]
        self.enabled_survey_fields = new_end_user_survey
        if save:
            self.save()

    @classmethod
    def add_job_template_survey_as_default_survey(cls, sender, instance, created, *args, **kwargs):
        if created:
            # copy the default survey and add a flag 'is_visible'
            default_survey = instance.job_template.survey
            end_user_survey = dict()
            if "spec" in default_survey:
                for survey_field in default_survey["spec"]:
                    end_user_survey[survey_field["variable"]] = True
            instance.enabled_survey_fields = end_user_survey
            instance.save()

    @classmethod
    def update_survey_after_job_template_update(cls, job_template):
        # get all operation that use the target job template
        operations = Operation.objects.filter(job_template=job_template)
        for operation in operations:
            operation.update_survey()


post_save.connect(Operation.add_job_template_survey_as_default_survey, sender=Operation)


@receiver(pre_save, sender=Operation)
def on_change(sender, instance: Operation, **kwargs):
    if instance.job_template is None and instance.type == OperationType.CREATE:
        instance.service.enabled = False
        instance.service.save()
    if instance.id is not None:
        previous = Operation.objects.get(id=instance.id)
        if previous.job_template != instance.job_template:
            instance.update_survey(save=False)
        if previous.enabled_survey_fields != instance.enabled_survey_fields:
            for request in instance.request_set.all():
                request.set_fill_in_survey(request.full_survey, instance.enabled_survey_fields)
