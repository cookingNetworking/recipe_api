"""Serializer for recipe!"""

from rest_framework import serializers

from core.models import Recipe, RecipePhoto, RecipeStep ,Tag, Ingredient


class TagSerialzier(serializers.ModelSerialzier):
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

class RecipeSerialzier(serializers.ModelSerializer):
    """Serialzier for recipe!!"""
    tag = TagSerialzier(many=True, required=False)
    ingredient = IngredientSerialzier(many=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'title','cost_time', 'description', 'ingredients', 'tags',]
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
            ingredient_obj = Ingredient.objects.create(
                **ingredient
            )
            recipe.ingredient.add(ingredient_obj)

    def create(self, validated_data):
        """Create recipe."""
        tags = validated_data.pop("tag", [])
        ingredients = validated_data.pop("ingredient", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop("tag", [])
        ingredients = validated_data.pop("ingredient", [])
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    class Meta:
        fields = RecipeSerialzier.Meta.fields + ['likes','save','views']

class RecipePhotoSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipePhoto!"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    class Meta:
        model = RecipePhoto
        fields = ['id', 'recipe', 'photo', 'upload_date', 'category']
        read_only_fields = ['id',]
        extra_kwargs = {"photo": {"required": True}}

class RecipeStepSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipeStep!"""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    class Meta:
        model = RecipeStep
        fields = ['id', 'recipe', 'step', 'description', 'image']
        read_only_fields = ['id']
        extra_kwargs = {"description": {"required": True}}