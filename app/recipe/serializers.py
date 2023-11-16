"""Serializer for recipe!"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import Recipe, RecipePhoto, RecipeStep ,Tag, Ingredient, RecipeComment
from .utils import CustomSlugRelatedField
from .redis_set import RedisHandler

import django_redis

redis_client1 = django_redis.get_redis_connection("default")

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username']

class TagSerialzier(serializers.ModelSerializer):
    """Serializer for recipe tags!"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'save_count', 'views']
        read_only_fields = ['id']

class IngredientSerialzier(serializers.ModelSerializer):
    """Serialzier for ingredient!"""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'save_count', 'views']
        read_only_fields = ['id']

class RecipeStepSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipeStep!"""
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = RecipeStep
        fields = ['id','recipe', 'step', 'description', 'image']
        read_only_fields = ['id','recipe']
        extra_kwargs = {"description": {"required": True}}

class RecipePhotoSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipePhoto!"""
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = RecipePhoto
        fields = ['id','recipe', 'photo', 'upload_date', 'category']
        read_only_fields = ['id','recipe']


class RecipeSerialzier(serializers.ModelSerializer):
    """Serialzier for recipe!!"""
    tags = CustomSlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all()
    )
    ingredients = CustomSlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Ingredient.objects.all()
    )
    photos = RecipePhotoSerialzier(many=True, required=False)
    steps = RecipeStepSerialzier(many=True, required=False)
    user = UserMinimalSerializer(read_only=True)
    class Meta:
        model = Recipe
        fields = ['id','user', 'title','cost_time', 'description', 'ingredients', 'tags','photos','steps']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or tags as needed."""
        for tag in tags:
            tag_obj,created = Tag.objects.get_or_create(
                name=tag
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                name=ingredient
            )
            recipe.ingredients.add(ingredient_obj)

    def _get_or_create_photos(self, photos, recipe):
        """Handle getting or creating photos as needed."""
        for photo in photos:
            photo_obj, created = RecipePhoto.objects.get_or_create(
                recipe=recipe,
                **photo
            )
    def _get_or_create_steps(self, steps, recipe):
        """Handle getting or creating steps as needed."""
        for step in steps:
            RecipeStep.objects.get_or_create(
                recipe=recipe,
                **step
            )

    def create(self, validated_data):
        """Create recipe."""
        req_user = self.context['request'].user
        req_tags = validated_data.pop("tags", [])
        print(req_tags)
        req_ingredients = validated_data.pop("ingredients", [])
        print(req_ingredients)
        photos = validated_data.pop("photos", [])
        steps = validated_data.pop("steps", [])

        recipe = Recipe.objects.create(user=req_user, **validated_data)
        self._get_or_create_tags(req_tags, recipe)
        self._get_or_create_ingredients(req_ingredients, recipe)
        self._get_or_create_photos(photos, recipe)
        self._get_or_create_steps(steps, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop("tag", [])
        ingredients = validated_data.pop("ingredient", [])
        photos = validated_data.pop("photo", [])
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)
        if photos is not None:
            instance.photos.clear()
            self._get_or_create_photos(photos, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class RecipeMinialSerialzier(serializers.ModelSerializer):
    """Serializer for only quert recipe title and id."""
    class Meta:
        model = Recipe
        fields = ["id", "title", 'user']

class RecipeCommentSerializer(serializers.ModelSerializer):
    """Serializer for recipe comment."""
    user = UserMinimalSerializer(read_only=True)
    recipe = RecipeMinialSerialzier(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Recipe.objects.all(),
        source='recipe'
    )
    class Meta:
        model = RecipeComment
        fields=["id", "recipe_id","user", "recipe", "comment", "rating", "Photo", "crated_time"]

    def create(self, validated_data):
        """Create with serializer"""
        req_user = self.context["request"].user
        recipe_id = self.context.get("recipe_id")
        recipe = Recipe.objects.get(id=recipe_id) if recipe_id else None
        if recipe:
            comment = RecipeComment.objects.create(user=req_user, recipe=recipe, **validated_data)
            return comment
        else:
            raise serializers.ValidationError("Recipe is required to create a comment")

class ReciperRedisDetailSerializer(serializers.Serializer):
    """Serializer for recipe detail !"""
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=30)
    cost_time = serializers.CharField(max_length=50)
    description = serializers.CharField(max_length=255)
    create_time = serializers.DateTimeField(required=False)
    user = UserMinimalSerializer(read_only=True)
    ingredients = serializers.ListField(child=serializers.CharField(max_length=100))
    tags = serializers.ListField(child=serializers.CharField(max_length=100))

    views = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    save_count = serializers.SerializerMethodField()
    recipe_comment = RecipeCommentSerializer(many=True, required=False)
    photos = RecipePhotoSerialzier(many=True, required=False)
    steps = RecipeStepSerialzier(many=True, required=False)

    recipe_redis_handler = RedisHandler(redis_client=redis_client1)

    class Meta:
        model = None
        fields = ['id','user', 'title','cost_time', 'description', 'ingredients', 'tags','photos','steps','likes','save_count','views', 'recipe_comment']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_views(self, obj):
        """Get recipe views from redis"""
        print(obj)
        return self.recipe_redis_handler.get_hkey(hkey_name='views',recipe_id=obj['id'])

    def get_likes(self, obj):
        """Get recipe likes from redis"""
        print(obj)
        return self.recipe_redis_handler.get_hkey(hkey_name='likes',recipe_id=obj['id'])

    def get_save_count(self, obj):
        """Get recipe likes from redis"""
        print(obj)
        return self.recipe_redis_handler.get_hkey(hkey_name='save_count',recipe_id=obj['id'])


class ReciperSQLDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    recipe_comment = RecipeCommentSerializer(many=True, required=False,read_only=True)
    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['create_time','likes','save_count','views', 'recipe_comment']




class LikeRecipeAction(serializers.Serializer):
    """Serializer for like action"""
    id = serializers.IntegerField(help_text="The ID of the recipe to like.")

class SaveActionSerializer(serializers.Serializer):
    """Serializer fot save action"""
    recipe_id = serializers.IntegerField(help_text="The ID of the recipe to like.", required=False)
    tag = serializers.CharField(help_text="tag name", required=False)
    ingredient = serializers.CharField(help_text="ingredient name", required=False)

class ResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="A success message.")
    error = serializers.CharField(help_text="A error message.")
    detail = serializers.CharField(help_text="A detail message.")