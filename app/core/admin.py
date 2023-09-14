"""
Admin for customer admin.
"""


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models

class UserAdmin(BaseUserAdmin):
    """Define the admin pages for ussers."""
    ordering = ["id"]
    list_display = ["email", "username"]
    fieldsets = (
        (None, {"fields":("email", "password",)}),
        (_('Personal Info'),{"fields":('username','role',)}),
        (_("Permission"),{"fields":('is_active','is_staff','is_superuser','groups','user_permissions')}),
        (_("Importnat Date"),{"fields":('last_login',)})
    )
    readonly_fields = ['last_login']
    add_fieldsets = [
        (None, {
            'classes':('wide',),
            'fields':(
                'email',
                'password1',
                'password2',
                'username',
                'is_staff',
                'is_superuser',
                'is_active',
                'role',
            )
        })
    ]


admin.site.register(models.User, UserAdmin)