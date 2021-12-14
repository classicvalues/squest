from guardian.shortcuts import get_objects_for_user
from rest_framework.generics import get_object_or_404
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, CharField, ValidationError

from profiles.models import BillingGroup
from service_catalog.forms import FormUtils
from service_catalog.models import Request, Service, OperationType, Operation, Instance
from service_catalog.serializers.dynamic_survey_serializer import DynamicSurveySerializer
from service_catalog.serializers.instance_serializer import InstanceSerializer


class ServiceRequestSerializer(ModelSerializer):
    class Meta:
        model = Request
        fields = ['instance_name', 'billing_group', 'fill_in_survey']

    instance_name = CharField(
        label="Squest instance name",
        help_text="Help to identify the requested service in the 'Instances' view"
    )
    billing_group = PrimaryKeyRelatedField(label='billing group id', allow_null=True, default=None, required=False,
                                           queryset=BillingGroup.objects.all(),
                                           help_text="Billing group id")

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context', None)
        self.view = context.get('view', None)
        self.service_id = self.view.kwargs.get('pk', None)
        self.request = context.get('request', None)
        super(ServiceRequestSerializer, self).__init__(*args, **kwargs)
        self.service = get_object_or_404(Service.objects.filter(enabled=True), id=self.service_id)
        # get the create operation of this service
        self.create_operation = Operation.objects.get(service=self.service, type=OperationType.CREATE)
        # get all field that are not disabled by the admin
        purged_survey = FormUtils.get_available_fields(job_template_survey=self.create_operation.job_template.survey,
                                                       operation_survey=self.create_operation.enabled_survey_fields)
        self.fields['fill_in_survey'] = DynamicSurveySerializer(fill_in_survey=purged_survey)

    def validate_billing_group(self, value):
        if not self.service.billing_group_is_selectable:
            return None if self.service.billing_group_id is None else BillingGroup.objects.get(
                id=self.service.billing_group_id)
        if value is not None:
            if self.service.billing_groups_are_restricted and value not in self.request.user.billing_groups.all():
                raise ValidationError(
                    f"You are not authorized to request this service with the billing group {value.name}. "
                    f"Please choose among yours"
                )
        return value

    def save(self):
        # create the instance
        instance_name = self.validated_data["instance_name"]
        billing_group = None
        if self.validated_data["billing_group"]:
            billing_group = self.validated_data["billing_group"]

        new_instance = Instance.objects.create(service=self.service, name=instance_name, billing_group=billing_group,
                                               spoc=self.request.user)
        # create the request
        new_request = Request.objects.create(instance=new_instance,
                                             operation=self.create_operation,
                                             fill_in_survey=self.validated_data["fill_in_survey"],
                                             user=self.request.user)
        return new_request


class OperationRequestSerializer(ModelSerializer):
    class Meta:
        model = Request
        fields = ['fill_in_survey']

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context', None)
        self.view = context.get('view', None)
        self.request = context.get('request', None)
        operation_id = self.view.kwargs.get('operation_id', None)
        instance_id = self.view.kwargs.get('instance_id', None)
        super(OperationRequestSerializer, self).__init__(*args, **kwargs)

        self.target_operation = get_object_or_404(Operation.objects.exclude(type=OperationType.CREATE), id=operation_id)
        self.target_instance = get_object_or_404(
            get_objects_for_user(self.request.user, 'service_catalog.view_instance'), id=instance_id)

        # get all field that are not disabled by the admin
        purged_survey = FormUtils.get_available_fields(job_template_survey=self.target_operation.job_template.survey,
                                                       operation_survey=self.target_operation.enabled_survey_fields)
        self.fields['fill_in_survey'] = DynamicSurveySerializer(fill_in_survey=purged_survey)

    def save(self, **kwargs):
        new_request = Request.objects.create(instance=self.target_instance,
                                             operation=self.target_operation,
                                             fill_in_survey=self.validated_data["fill_in_survey"],
                                             user=self.request.user)
        return new_request


class RequestSerializer(ModelSerializer):
    class Meta:
        model = Request
        exclude = ['periodic_task', 'periodic_task_date_expire', 'failure_message']
        read_only = True

    instance = InstanceSerializer(read_only=True)


class AdminRequestSerializer(ModelSerializer):
    class Meta:
        model = Request
        exclude = ['periodic_task', 'periodic_task_date_expire', 'failure_message']

    instance = InstanceSerializer(read_only=True)