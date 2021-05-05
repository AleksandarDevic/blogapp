from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class WriterHasEditorPermission(BasePermission):
    def has_permission(self, request, view):
        group_list = []
        user_group_qs = request.user.groups.all()
        if user_group_qs:
            for g in user_group_qs:
                group_list.append(g.name)
        if 'Editor' in group_list:
            return True
        else:
            # return redirect('dashboard')
            # return HttpResponse('You are not authorized to view this page!')
            raise PermissionDenied('You are not authorized to view this page!')
