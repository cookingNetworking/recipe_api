"""
Database models.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)

import uuid

ROLL =( ('admin','Admin'), ('cook','Cook'), ('user','User') )

def generate_prefixed_uuid():
    return f"test_{uuid.uuid4()}"

def test_upload_image_file_path(instance, filename):
    """Generate a filepath for recipe image."""

    return f'test/{instance.uuid}/{filename}'

def upload_image_file_path(instance, filename):
    """Generate a filepath for recipe image."""
    return f'recipes/{instance.id}/{filename}'

def step_image_file_path(instance, filename):
    """Generate a filepath for recipe step image."""
    return f'recipe/{instance.recipe}/{instance.step}/{filename}'

class UserManager(BaseUserManager):
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
    create = models.DateTimeField(auto_now_add=True,null=True,blank= True)
    objects = UserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class UserFollowing(models.Model):
    """Establish users releationship."""
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="following",on_delete=models.CASCADE)
    following_user_id = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="follower",on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True,null=True,blank= True)

class Recipe(models.Model):
    """Recipe object!"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    title = models.CharField(max_length=30, unique=True)
    cost_time = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    create_time = models.DateTimeField(auto_now_add=True,null=True,blank= True)
    ingredients = models.ManyToManyField("Ingredient")
    tags = models.ManyToManyField('Tag')
    likes = models.IntegerField(default=0)
    save = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    photo = models.ImageField(null=True, upload_to=upload_image_file_path)
    def __str__(self):
        return self.title

class RecipeStep(models.Model):
    """Step for recipe."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    step = models.SmallIntegerField(default=1, null=False)
    description = models.TextField(max_length=500, null=False)
    image = models.ImageField(null=True, upload_to=step_image_file_path)

    def __str__(self):
        return f'{self.recipe}step_{self.step}'


class Ingredient(models.Model):
    """Ingredient for recipes."""
    name = models.CharField(max_length=50)
    save = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    def __str__(self):
        return self.name

class Tag(models.Model):
    """Tags for filter recipe."""
    name = models.CharField(max_length=50)
    save = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    def __str__(self):
        return self.name

class TestImageUpload(models.Model):
    uuid = models.CharField(max_length=50, default=generate_prefixed_uuid, editable=False, unique=True)
    name = models.CharField(max_length=15, default="name")
    image = models.ImageField(null=True,  upload_to=test_upload_image_file_path)