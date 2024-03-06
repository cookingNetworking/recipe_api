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

RATING = ((1,'*'),(2,'**'),(3,'***'),(4,'****'),(5,'*****'))

def generate_prefixed_uuid():
    return f"test_{uuid.uuid4()}"

def test_upload_image_file_path(instance, filename):
    """Generate a filepath for recipe image."""
    return f'test/{instance.uuid}/{filename}'

def upload_image_file_path(instance, filename):
    """Generate a filepath for recipe image."""
    return f'recipes/{instance.recipe}/{filename}'

def step_image_file_path(instance, filename):
    """Generate a filepath for recipe step image."""
    return f'recipes/{instance.recipe}/{instance.step}/{filename}'

def comment_image_file_path(instance, filename):
    return f'recipe/{instance.recipe}/comment{filename}'

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
    title = models.CharField(max_length=30)
    cost_time = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    create_time = models.DateTimeField(auto_now_add=True,null=True,blank= True)
    ingredients = models.ManyToManyField("Ingredient")
    tags = models.ManyToManyField('Tag')
    likes = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    def __str__(self):
        return self.title

    @property
    def all_photo(self):
        return self.photos.all()

    def total_likes(self):
        return self.recipe_be_liked.count()

class RecipeComment(models.Model):
    """
    The relatrionship for user and recipe which  user could make a comment!
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_comment")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_comment")
    comment = models.TextField(blank=True)
    rating = models.IntegerField(choices=RATING, default="1", help_text="rating form 1 to 5")
    Photo = models.ImageField(null=True, blank=True, upload_to=comment_image_file_path)
    created_time = models.DateTimeField(auto_now=True)

class Like(models.Model):
    """
    The relationship of user and recipe.
    Like.objects.filter(recipe=specific_recipe).count() => get all likes of recipe!
    Like.objects.filter(user=specific_user).count => gel all recipe liked by user!
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_likes")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_be_liked")

    class Meta:
        unique_together = ('user', 'recipe') #like add constrain  CONSTRAINT unique_user_recipe UNIQUE (user_id, recipe_id)

    def __str__(self):
        return f'{self.user.username} likes {self.recipe.title}'

class Save(models.Model):
    """
    The table record user saved which recipe, tags, ingredients!
    In this table, user only can save same recipe, ingredient, tag for more than one time.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_save", blank=True, null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="saved_recipe", blank=True, null=True)
    tag = models.ForeignKey("Tag", on_delete=models.CASCADE, related_name="saved_tag", blank=True, null=True)
    ingredient = models.ForeignKey("Ingredient", on_delete=models.CASCADE, related_name="saved_ingredient", blank=True, null=True)

    class Meta:
        unique_together = [
            ("user", "recipe"),
            ("user", "tag"),
            ("user", "ingredient")
        ]

class CoverImage(models.Model):
    """Recipe photo show on recipe page!"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(null=True, upload_to=upload_image_file_path)
    upload_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class RecipeStep(models.Model):
    """Step for recipe."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    step = models.SmallIntegerField(default=1, null=False)
    description = models.TextField(max_length=500, null=False)
    image = models.ImageField(null=True, upload_to=step_image_file_path)

    def __str__(self):
        return f'{self.recipe}_{self.step}'


class Ingredient(models.Model):
    """Ingredient for recipes."""
    name = models.CharField(max_length=50)
    save_count = models.IntegerField(default=0)
    views = models.IntegerField(default=1)
    def __str__(self):
        return self.name

class Tag(models.Model):
    """Tags for filter recipe."""
    name = models.CharField(max_length=50)
    save_count = models.IntegerField(default=0)
    views = models.IntegerField(default=1)
    def __str__(self):
        return self.name

class TestImageUpload(models.Model):
    uuid = models.CharField(max_length=50, default=generate_prefixed_uuid, editable=False)
    name = models.CharField(max_length=15, default="name")
    image = models.ImageField(null=True,  upload_to=test_upload_image_file_path)


class Notification(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    delievered = models.BooleanField(default=False)
    def __str__(self):
        return f"Notification {self.title} to {self.client.username}"
