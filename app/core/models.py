"""
Database models.
"""
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)

ROLL =( ('admin','Admin'), ('cook','Cook'), ('user','User') )

class  UserManager(BaseUserManager):
    """Manage for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create user and return a new user."""
        if not email:
            raise ValueError("User must have email!!!")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    def create_superuser(self, email, password):
        """Create superuser and return."""
        if not email:
            raise ValueError("User must have email!!!")
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in this system."""
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255,unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(choices=ROLL,max_length=10,default='user')
    birthday = models.DateField(null=True,blank=True)
    
    objects = UserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
