"""
Admin for customer admin.
"""


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models
from django.contrib.sessions.models import Session

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expire_date', 'session_data')
    readonly_fields = ('session_key', 'expire_date', 'session_data')

@admin.register(models.TestImageUpload)
class TestImageUploadAdmin(admin.ModelAdmin):
    list_display = ('name','image','uuid')

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

admin.site.register(models.Recipe)
admin.site.register(models.CoverImage)
admin.site.register(models.RecipeStep)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient)
admin.site.register(models.Save)
admin.site.register(models.Like)
admin.site.register(models.RecipeComment)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserFollowing)
admin.site.register(models.Notification)