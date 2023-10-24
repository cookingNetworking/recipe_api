"""Serializer for recipe!"""

from rest_framework import serializers

from core.models import Recipe, RecipePhoto, RecipeStep ,Tag, Ingredient


class TagSerialzier(serializers.ModelSerializer):
    """Serializer for recipe tags!"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'save', 'views']
        read_only_fields = ['id']

class IngredientSerialzier(serializers.ModelSerializer):
    """Serialzier for ingredient!"""
    class Meta:
        models = Ingredient
        fields = ['id', 'name', 'save', 'views']
        read_only_fields = ['id']

class RecipeStepSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipeStep!"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    class Meta:
        model = RecipeStep
        fields = ['id', 'recipe', 'step', 'description', 'image']
        read_only_fields = ['id']
        extra_kwargs = {"description": {"required": True}}

class RecipePhotoSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipePhoto!"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    class Meta:
        model = RecipePhoto
        fields = ['id', 'recipe', 'photo', 'upload_date', 'category']
        read_only_fields = ['id',]


class RecipeSerialzier(serializers.ModelSerializer):
    """Serialzier for recipe!!"""
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Tag.objects.all()
    )
    ingredients = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Ingredient.objects.all()
    )
    photos = RecipeStepSerialzier(many=True, required=True)
    steps = RecipeStepSerialzier(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'title','cost_time', 'description', 'ingredients', 'tags','photos','steps']
        read_only_fields = ['id',]

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or tags as needed."""
        for tag in tags:
            tag_obj,created = Tag.objects.get_or_create(
                **tag
            )
            recipe.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                **ingredient
            )
            recipe.ingredient.add(ingredient_obj)

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
        tags = validated_data.pop("tag", [])
        ingredients = validated_data.pop("ingredient", [])
        photos = validated_data.pop("photo", [])
        steps = validated_data.pop("steps", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
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

class RecipeDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['likes','save','views']



