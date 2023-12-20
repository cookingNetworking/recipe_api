"""Serializer for recipe!"""
from decimal import Decimal
from storages.backends.s3boto3 import S3Boto3Storage
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg
from core.models import Recipe, RecipePhoto, RecipeStep ,Tag, Ingredient, RecipeComment
from .utils import CustomSlugRelatedField

s3_storage = S3Boto3Storage()
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
    recipe_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecipeStep
        fields = ['id','recipe_id', 'step', 'description', 'image', ]
        read_only_fields = ['id','recipe_id']
        extra_kwargs = {"description": {"required": True}}

    def get_signed_photo_url(self, obj):
        if obj.image :
            return s3_storage.url(str(obj.image), expire=1800)
        return None

class RecipePhotoSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipePhoto!"""
    recipe_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RecipePhoto
        fields = ['id','recipe_id', 'photo', 'upload_date', 'category']
        read_only_fields = ['id','recipe_id','upload_date']


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
    comment_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2,required=False)
    class Meta:
        model = Recipe
        fields = ['id','user', 'title', 'cost_time', 'description', 'ingredients', 'tags', 'photos', 'steps', 'comment_count', 'average_rating']
        read_only_fields = ['id','comment_count', 'average_rating']

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
        req_ingredients = validated_data.pop("ingredients", [])
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
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        photos = validated_data.pop("photos", [])
        steps = validated_data.pop("steps", [])
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)
        if photos is not None:
            RecipePhoto.objects.filter(recipe=instance).delete()
            self._get_or_create_photos(photos, instance)
        if steps is not None:
            RecipeStep.objects.filter(recipe=instance).delete()
            self._get_or_create_steps(steps, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class RecipeMinialSerialzier(serializers.ModelSerializer):
    """Serializer for only quert recipe title and id."""
    class Meta:
        model = Recipe
        fields = ["id"]

class RecipeCommentSerializer(serializers.ModelSerializer):
    """Serializer for recipe comment."""
    user = UserMinimalSerializer(read_only=True)
    recipe = CustomSlugRelatedField(
        many=False,
        slug_field='id',
        queryset=Recipe.objects.all()
    )
    class Meta:
        model = RecipeComment
        fields=["id", "recipe","user", "comment", "rating", "Photo", "created_time"]
        extra_kwargs = {"rating": {"required": True}}


    def create(self, validated_data):
        """Create with serializer"""
        req_user = self.context["request"].user
        recipe = validated_data.pop("recipe",None)
        # recipe = Recipe.objects.get(id=recipe_id) if recipe_id else None
        if recipe:
            comment = RecipeComment.objects.create(user=req_user, recipe=recipe, **validated_data)
            return comment
        else:
            raise serializers.ValidationError("Recipe is required to create a comment")


class RecipeSQLDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    top_five_comments = serializers.SerializerMethodField()

    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['create_time','likes','save_count','views', 'top_five_comments']
        read_only_fields = RecipeSerialzier.Meta.read_only_fields + ['likes','save_count','views','top_five_comments']

    def get_top_five_comments(self, obj):
        comments = obj.recipe_comment.order_by('-created_time')[:5]
        return RecipeCommentSerializer(comments, many=True).data

class LikeRecipeAction(serializers.Serializer):
    """Serializer for like action"""
    recipe_id = serializers.IntegerField(help_text="The ID of the recipe to like.")

class SaveActionSerializer(serializers.Serializer):
    """Serializer fot save action"""
    recipe_id = serializers.IntegerField(help_text="The ID of the recipe to like.", required=False)
    tag = serializers.CharField(help_text="tag name", required=False)
    ingredient = serializers.CharField(help_text="ingredient name", required=False)

class ResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="A success message.")
    error = serializers.CharField(help_text="A error message.")
    detail = serializers.CharField(help_text="A detail message.")