from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_fsm import can_proceed
from guardian.decorators import permission_required_or_403

from profiles.forms import UserRoleForObjectForm, TeamRoleForObjectForm
from profiles.models import Role, Team
from profiles.tables import TeamsByObjectTable
from profiles.tables import UserByObjectTable
from service_catalog.forms import InstanceForm, OperationRequestForm, SupportRequestForm
from service_catalog.forms.common_forms import SupportMessageForm
from service_catalog.models import Instance, Support, Operation, InstanceState, OperationType, SupportMessage, Request
from service_catalog.tables.operation_tables import OperationTableFromInstanceDetails
from service_catalog.tables.request_tables import RequestTable
from service_catalog.views.support_list_view import SupportTable


@user_passes_test(lambda u: u.is_superuser)
def instance_edit(request, instance_id):
    instance = get_object_or_404(Instance, id=instance_id)
    form = InstanceForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('service_catalog:instance_details', instance.id)
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': f"{instance.name} ({instance.id})",
         'url': reverse('service_catalog:instance_details', args=[instance_id])},
    ]
    context = {'form': form, 'breadcrumbs': breadcrumbs}
    return render(request, 'service_catalog/admin/instance/instance-edit.html', context)


@user_passes_test(lambda u: u.is_superuser)
def instance_delete(request, instance_id):
    instance = get_object_or_404(Instance, id=instance_id)
    if request.method == 'POST':
        instance.delete()
        return redirect("service_catalog:instance_list")
    args = {
        "instance_id": instance_id,
    }
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': f"{instance.name} ({instance.id})",
         'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': 'Delete', 'url': ''}
    ]
    context = {
        'breadcrumbs': breadcrumbs,
        'confirm_text': mark_safe(f"Confirm deletion of <strong>{instance.name}</strong>?"),
        'action_url': reverse('service_catalog:instance_delete', kwargs=args),
        'button_text': 'Delete',
        'details':
            {
                'warning_sentence': 'Warning: all requests related to this instance will be deleted:',
                'details_list': [f"ID: {request.id}, State: {request.state}" for request in instance.request_set.all()]
            } if instance.request_set.count() != 0 else None
    }
    return render(request, 'generics/confirm-delete-template.html', context=context)


@login_required
@permission_required_or_403('service_catalog.request_operation_on_instance', (Instance, 'id', 'instance_id'))
def instance_request_new_operation(request, instance_id, operation_id):
    instance = get_object_or_404(Instance, id=instance_id)
    if instance.state not in [InstanceState.AVAILABLE, InstanceState.UPDATING]:
        raise PermissionDenied
    operation = get_object_or_404(Operation, id=operation_id)
    allowed_operations = Operation.objects.filter(service=instance.service,
                                                  type__in=[OperationType.UPDATE, OperationType.DELETE])
    if operation not in allowed_operations:
        raise PermissionDenied
    parameters = {
        'operation_id': operation_id,
        'instance_id': instance_id
    }
    if request.method == 'POST':
        form = OperationRequestForm(request.user, request.POST, **parameters)
        if form.is_valid():
            form.save()
            return redirect('service_catalog:request_list')
    else:
        form = OperationRequestForm(request.user, **parameters)
    context = {'form': form, 'operation': operation, 'instance': instance}
    return render(request, 'service_catalog/customer/instance/instance-request-operation.html', context)


@login_required
@permission_required_or_403('service_catalog.delete_instance', (Instance, 'id', 'instance_id'))
def instance_archive(request, instance_id):
    target_instance = get_object_or_404(Instance, id=instance_id)
    if request.method == "POST":
        if not can_proceed(target_instance.archive):
            raise PermissionDenied
        target_instance.archive()
        target_instance.save()

        return redirect('service_catalog:instance_list')
    context = {
        "instance": target_instance
    }
    return render(request, "service_catalog/customer/instance/instance-archive.html", context)


@login_required
@permission_required_or_403('service_catalog.request_support_on_instance', (Instance, 'id', 'instance_id'))
def instance_new_support(request, instance_id):
    target_instance = get_object_or_404(Instance, id=instance_id)
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': f"{target_instance.name} ({target_instance.id})",
         'url': reverse('service_catalog:instance_details', args=[instance_id])},
    ]
    parameters = {
        'instance_id': instance_id
    }
    if request.method == 'POST':
        form = SupportRequestForm(request.user, request.POST, **parameters)
        if form.is_valid():
            form.save()
            return redirect('service_catalog:instance_details', target_instance.id)
    else:
        form = SupportRequestForm(request.user, **parameters)
    context = {'form': form, 'instance': target_instance, 'breadcrumbs': breadcrumbs}
    return render(request, 'service_catalog/common/support-create.html', context)


@login_required
@permission_required_or_403('service_catalog.request_support_on_instance', (Instance, 'id', 'instance_id'))
def instance_support_details(request, instance_id, support_id):
    instance = get_object_or_404(Instance, id=instance_id)
    support = get_object_or_404(Support, id=support_id)
    messages = SupportMessage.objects.filter(support=support)
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': f"{instance.name} ({instance.id})",
         'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': 'Support', 'url': ""},
        {'text': support.title, 'url': ""},
    ]
    if request.method == "POST":
        form = SupportMessageForm(request.POST or None)
        if "btn_close" in request.POST:
            if not can_proceed(support.do_close):
                raise PermissionDenied
            support.do_close()
            support.save()
        if "btn_re_open" in request.POST:
            if not can_proceed(support.do_open):
                raise PermissionDenied
            support.do_open()
            support.save()
        if form.is_valid():
            if form.cleaned_data["content"] is not None and form.cleaned_data["content"] != "":
                new_message = form.save()
                new_message.support = support
                new_message.sender = request.user
                new_message.save()
            return redirect('service_catalog:instance_support_details', instance.id, support.id)
    else:
        form = SupportMessageForm()
    context = {
        "form": form,
        "instance": instance,
        "messages": messages,
        "support": support,
        'breadcrumbs': breadcrumbs
    }
    return render(request, "service_catalog/common/instance-support-details.html", context)


@login_required
@permission_required_or_403('service_catalog.view_instance', (Instance, 'id', 'instance_id'))
def instance_details(request, instance_id):
    instance = get_object_or_404(Instance, id=instance_id)
    supports = Support.objects.filter(instance=instance)
    operations = Operation.objects.filter(service=instance.service,
                                          type__in=[OperationType.UPDATE, OperationType.DELETE])
    requests = Request.objects.filter(instance=instance)
    operations_table = OperationTableFromInstanceDetails(operations)
    requests_table = RequestTable(requests,
                                  hide_fields=["instance__name", "instance__service__name"])
    supports_table = SupportTable(supports, hide_fields=["instance__name"])

    users_table = UserByObjectTable(instance.get_all_users())
    teams_table = TeamsByObjectTable(instance.get_all_teams())
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': f"{instance.name} ({instance.id})", 'url': ""},
    ]
    context = {'instance': instance,
               'operations_table': operations_table,
               'requests_table': requests_table,
               'supports_table': supports_table,
               'users_table': users_table,
               'teams_table': teams_table,
               'user_roles': instance.get_roles_of_users(),
               'team_roles': instance.get_roles_of_teams(),
               'app_name': 'service_catalog',
               'object': instance,
               'object_name': 'instance',
               'object_id': instance.id,
               'breadcrumbs': breadcrumbs,
               }
    return render(request, 'service_catalog/common/instance-details.html', context=context)


@login_required
@permission_required_or_403('service_catalog.change_instance', (Instance, 'id', 'instance_id'))
def user_in_instance_update(request, instance_id):
    instance = get_object_or_404(Instance, id=instance_id)
    form = UserRoleForObjectForm(request.POST or None, object=instance)
    error = False
    if request.method == 'POST':
        if form.is_valid():
            users_id = form.cleaned_data.get('users')
            role_id = int(form.cleaned_data.get('roles'))
            role = Role.objects.get(id=role_id)
            current_users = instance.get_users_in_role(role.name)
            selected_users = [User.objects.get(id=user_id) for user_id in users_id]
            to_remove = list(set(current_users) - set(selected_users))
            to_add = list(set(selected_users) - set(current_users))
            if instance.spoc in to_remove and role.name == "Admin":
                form.add_error('users', 'SPOC cannot be removed from Admin')
                error = True
            if not error:
                for user in to_add:
                    instance.add_user_in_role(user, role.name)
                for user in to_remove:
                    instance.remove_user_in_role(user, role.name)
                return redirect("service_catalog:instance_details", instance_id=instance_id)
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': instance.name, 'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': "Users", 'url': ""}
    ]
    context = {'form': form, 'content_type_id': ContentType.objects.get_for_model(Instance).id, 'object_id': instance.id,
               'breadcrumbs': breadcrumbs}
    return render(request, 'profiles/role/user-role-for-object-form.html', context)


@login_required
@permission_required_or_403('service_catalog.change_instance', (Instance, 'id', 'instance_id'))
def user_in_instance_remove(request, instance_id, user_id):
    instance = get_object_or_404(Instance, id=instance_id)
    user = User.objects.get(id=user_id)
    if user == instance.spoc:
        return redirect('service_catalog:instance_details', instance_id=instance_id)
    if request.method == 'POST':
        instance.remove_user_in_role(user)
        return redirect('service_catalog:instance_details', instance_id=instance_id)
    args = {
        "instance_id": instance_id,
        "user_id": user_id
    }
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': instance.name, 'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': "Users", 'url': ""}
    ]
    context = {
        'breadcrumbs': breadcrumbs,
        'confirm_text': mark_safe(f"Confirm to remove the user <strong>{user.username}</strong> from {instance}?"),
        'action_url': reverse('service_catalog:user_in_instance_remove', kwargs=args),
        'button_text': 'Remove'
    }
    return render(request, 'generics/confirm-delete-template.html', context=context)


@login_required
@permission_required_or_403('service_catalog.change_instance', (Instance, 'id', 'instance_id'))
def team_in_instance_update(request, instance_id):
    instance = get_object_or_404(Instance, id=instance_id)
    form = TeamRoleForObjectForm(request.POST or None, user=request.user, object=instance)
    if request.method == 'POST':
        if form.is_valid():
            teams_id = form.cleaned_data.get('teams')
            role_id = int(form.cleaned_data.get('roles'))
            role = Role.objects.get(id=role_id)
            current_teams = instance.get_teams_in_role(role.name)
            selected_teams = [Team.objects.get(id=team_id) for team_id in teams_id]
            to_remove = list(set(current_teams) - set(selected_teams))
            to_add = list(set(selected_teams) - set(current_teams))
            for team in to_add:
                instance.add_team_in_role(team, role.name)
            for team in to_remove:
                instance.remove_team_in_role(team, role.name)
            return redirect("service_catalog:instance_details", instance_id=instance_id)
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': instance.name, 'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': "Teams", 'url': ""}
    ]
    context = {'form': form, 'content_type_id': ContentType.objects.get_for_model(Instance).id, 'object_id': instance.id,
               'breadcrumbs': breadcrumbs}
    return render(request, 'profiles/role/team-role-for-object-form.html', context)


@login_required
@permission_required_or_403('service_catalog.change_instance', (Instance, 'id', 'instance_id'))
def team_in_instance_remove(request, instance_id, team_id):
    instance = get_object_or_404(Instance, id=instance_id)
    team = Team.objects.get(id=team_id)
    if team == instance.spoc:
        return redirect('service_catalog:instance_details', instance_id=instance_id)
    if request.method == 'POST':
        instance.remove_team_in_role(team)
        return redirect('service_catalog:instance_details', instance_id=instance_id)
    args = {
        "instance_id": instance_id,
        "team_id": team_id
    }
    breadcrumbs = [
        {'text': 'Instances', 'url': reverse('service_catalog:instance_list')},
        {'text': instance.name, 'url': reverse('service_catalog:instance_details', args=[instance_id])},
        {'text': "Teams", 'url': ""}
    ]
    context = {
        'breadcrumbs': breadcrumbs,
        'confirm_text': mark_safe(f"Confirm to remove the team <strong>{team.teamname}</strong> from {instance}?"),
        'action_url': reverse('service_catalog:team_in_instance_remove', kwargs=args),
        'button_text': 'Remove'
    }
    return render(request, 'generics/confirm-delete-template.html', context=context)