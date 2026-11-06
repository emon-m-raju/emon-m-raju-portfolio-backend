from rest_framework.permissions import BasePermission, SAFE_METHODS
class IsOwnerOrReadOnly(BasePermission):
 def has_permission(self, request, view):
  return request.method in SAFE_METHODS or bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class ContactSubmissionPermission(IsOwnerOrReadOnly):
 def has_permission(self, request, view):
  return request.method == 'POST' or super().has_permission(request, view)

class ContactMessagePermission(IsOwnerOrReadOnly):
 def has_permission(self, request, view):
  if getattr(view, 'action', None) == 'create':
   return request.method == 'POST'
  return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
