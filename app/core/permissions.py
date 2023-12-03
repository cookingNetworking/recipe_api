"""For Permission class"""

from rest_framework import permissions


class IsAdminOrRecipeOwmer(permissions.BasePermission):
    """Custom permission that allow only admin or recipeowner to manipulate """

    def has_object_permissions(self ,request, view, obj):
        if request.user.is_staff:
            return True

        return obj.user == request.user


