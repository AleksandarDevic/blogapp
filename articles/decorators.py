from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect


def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


def editor_only(view_func):
    def wrapper_func(request, *args, **kwargs):
        group_list = []
        user_group_qs = request.user.groups.all()
        if user_group_qs:
            for g in user_group_qs:
                group_list.append(g.name)
        if 'Editor' in group_list:
            return view_func(request, *args, **kwargs)
        else:
            # return redirect('dashboard')
            # return HttpResponse('You are not authorized to view this page!')
            raise PermissionDenied('You are not authorized to view this page!')

    return wrapper_func
