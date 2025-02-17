from rest_framework import  permissions

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_admin


class IsPartner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_partner
    
class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_client
    
class IsTeam(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_team
    
class IsEndUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_enduser

class IsEvent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_event