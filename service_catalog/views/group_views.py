from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe

from service_catalog.forms import GroupForm, AddUserForm


@user_passes_test(lambda u: u.is_superuser)
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'service_catalog/group/group-list.html', {'groups': groups})


@user_passes_test(lambda u: u.is_superuser)
def group_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    form = GroupForm(request.POST or None, instance=group)
    if form.is_valid():
        form.save()
        return redirect("service_catalog:group_list")
    return render(request, 'service_catalog/group/group-edit.html', {'form': form, 'group': group})


@user_passes_test(lambda u: u.is_superuser)
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_catalog:group_list")
    else:
        form = GroupForm()
    return render(request, 'service_catalog/group/group-create.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)
def group_delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.delete()
        return redirect("service_catalog:group_list")
    args = {
        "group_id": group_id,
    }
    context = {
        'title_text': 'Groups',
        'confirm_text': mark_safe(f"Confirm deletion of <strong>{group.name}</strong>?"),
        'action_url': reverse('service_catalog:group_delete', kwargs=args),
        'button_text': 'Delete',
        'details': {'warning_sentence': 'Warning: some users are still present in this group, see them below:',
                    'details_list': [user.username for user in group.user_set.all()]
                    } if group.user_set.all() else None
    }
    return render(request, 'service_catalog/group/confirm-delete-template.html', context=context)


@user_passes_test(lambda u: u.is_superuser)
def user_by_group_list(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    return render(request, 'service_catalog/group/user-by-group-list.html', {'group': group})


@user_passes_test(lambda u: u.is_superuser)
def user_in_group_update(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    form = AddUserForm(request.POST or None, current_users=group.user_set.all())
    if request.method == 'POST':
        if form.is_valid():
            users_id = form.cleaned_data.get('users')
            current_users = group.user_set.all()
            selected_users = [User.objects.get(id=user_id) for user_id in users_id]
            to_remove = list(set(current_users) - set(selected_users))
            to_add = list(set(selected_users) - set(current_users))
            for user in to_remove:
                group.user_set.remove(user)
            for user in to_add:
                group.user_set.add(user)
            return redirect("service_catalog:user_by_group_list", group_id=group_id)
    return render(request, 'service_catalog/group/user-in-group-update.html', {'form': form, 'group': group})


@user_passes_test(lambda u: u.is_superuser)
def user_in_group_remove(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        group.user_set.remove(user)
        return redirect('service_catalog:user_by_group_list', group_id=group_id)
    args = {
        "group_id": group_id,
        "user_id": user_id
    }
    context = {
        'title_text': f"Users in  { group }",
        'confirm_text': mark_safe(f"Confirm to remove the user <strong>{ user.username }</strong> from { group }?"),
        'action_url': reverse('service_catalog:user_in_group_remove', kwargs=args),
        'button_text': 'Delete'
    }
    return render(request, 'service_catalog/group/confirm-delete-template.html', context=context)