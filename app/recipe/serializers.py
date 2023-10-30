"""Serializer for recipe!"""

from rest_framework import serializers

from core.models import Recipe, RecipePhoto, RecipeStep ,Tag, Ingredient
from .utils import CustomSlugRelatedField
from .redis_set import get_recipe_view_hkey, get_recipe_like_hkey, get_recipe_save_count_hkey

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
    class Meta:
        model = Recipe
        fields = ['id', 'title','cost_time', 'description', 'ingredients', 'tags','photos','steps']
        read_only_fields = ['id',]

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

class ReciperRedisDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    views = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    save_count = serializers.SerializerMethodField()
    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['likes','save_count','views']

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.db = kwargs.get('context',{}).get('db', 'sql')

    def get_views(self, obj, db):
        """Get recipe views from redis"""
        return get_recipe_view_hkey(obj.id, 'views')


    def get_likes(self, obj):
        """Get recipe likes from redis"""
        return get_recipe_like_hkey(obj.id, 'likes')

    def get_save_count(self, obj):
        """Get recipe likes from redis"""
        return get_recipe_save_count_hkey(obj.id, 'save_count')


class ReciperSQLDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['likes','save_count','views']
