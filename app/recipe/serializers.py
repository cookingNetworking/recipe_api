"""Serializer for recipe!"""
from storages.backends.s3boto3 import S3Boto3Storage

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from core.models import (
                        Recipe,
                        CoverImage,
                        RecipeStep ,
                        Tag,
                        Ingredient,
                        RecipeComment,
                        Notification
                        )
from .utils import CustomSlugRelatedField

s3_storage = S3Boto3Storage()
class UserMinimalSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = get_user_model()
        fields = ['user_id', 'username']

class TagSerialzier(serializers.ModelSerializer):
    """Serializer for recipe tags!"""
    tag_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = Tag
        fields = ['tag_id', 'name', 'save_count', 'views']
        read_only_fields = ['tag_id']

class IngredientSerialzier(serializers.ModelSerializer):
    """Serialzier for ingredient!"""
    ingredient_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = Ingredient
        fields = ['ingredient_id', 'name', 'save_count', 'views']
        read_only_fields = ['ingredient_id']

class RecipeStepSerialzier(serializers.ModelSerializer):
    """Serialzier for RecipeStep!"""
    recipe_id = serializers.PrimaryKeyRelatedField(read_only=True)
    step_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = RecipeStep
        fields = ['step_id','recipe_id', 'step', 'description', 'photo', ]
        read_only_fields = ['step_id','recipe_id']
        extra_kwargs = {"description": {"required": True}}

    def get_signed_photo_url(self, obj):
        if obj.image :
            return s3_storage.url(str(obj.image), expire=1800)
        return None

class CoverImageSerialzier(serializers.ModelSerializer):
    """Serialzier for CoverImage!"""
    recipe_id = serializers.PrimaryKeyRelatedField(read_only=True)
    cov_img_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = CoverImage
        fields = ['cov_img_id','recipe_id', 'image', 'upload_date']
        read_only_fields = ['cov_img_id','recipe_id','upload_date']


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
    coverimage = CoverImageSerialzier(many=True, required=False)
    user = UserMinimalSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2,required=False)
    class Meta:
        model = Recipe
        fields = ['id','user', 'title', 'cost_time', 'description', 'ingredients', 'tags', 'coverimage','comment_count', 'average_rating']
        read_only_fields = ['id','comment_count', 'average_rating']


    def _extract_steps_data(self, data):
        """Extract steps data from request data."""
        steps_data = []
        for key in data.keys():
            if key.startswith('steps'):
                _, index, field = key.split('.')
                index = int(index)
                if len(steps_data) <= index:
                    steps_data.append({})
                steps_data[index][field] = data[key]
        for i in range(len(steps_data)):
            steps_data[i]['photo'] = self.context['request'].FILES.get(f'steps.{i}.photo')
        return steps_data

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

    
    def _get_or_create_coverimage(self, coverimage, recipe):
        """Handle getting or creating photos as needed."""
        try:
            for image_data in coverimage :
                if image_data and isinstance(image_data, UploadedFile):
                    CoverImage.objects.create(
                        recipe=recipe,
                        image=image_data,
                    )
        except Exception as e :
            print(e)
    def _get_or_create_steps(self, stepsphoto_files, recipe):
        """Handle getting or creating steps as needed."""
        for step_data in stepsphoto_files:
            try: 
                if step_data and isinstance(step_data['photo'], UploadedFile):
                    print("entry if", stepsphoto_files)
                    RecipeStep.objects.create(
                        recipe=recipe,
                        **step_data
                    )
            except Exception as e:
                print(e)

    def create(self, validated_data):
        """Create recipe."""
        req_user = self.context['request'].user
        req_tags = validated_data.pop("tags", [])
        req_ingredients = validated_data.pop("ingredients", [])
        coverimage_files = self.context['request'].FILES.getlist('cover_image')
        stepsphoto_files = validated_data.pop("steps", [])
        recipe = Recipe.objects.create(user=req_user, **validated_data)
        self._get_or_create_tags(req_tags, recipe)
        self._get_or_create_ingredients(req_ingredients, recipe)
        self._get_or_create_coverimage(coverimage_files, recipe)
        self._get_or_create_steps(stepsphoto_files, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        coverimage_files = self.context['request'].FILES.getlist('cover_image')
        stepsphoto_files = validated_data.pop("steps", [])
        if tags:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)
        if coverimage_files :
            CoverImage.objects.filter(recipe=instance).delete()
            self._get_or_create_coverimage(coverimage_files, instance)
        if stepsphoto_files :
            RecipeStep.objects.filter(recipe=instance).delete()
            self._get_or_create_steps(stepsphoto_files, instance)
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
    comment_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = RecipeComment
        fields=["comment_id", "recipe","user", "comment", "rating","created_time"]
        extra_kwargs = {"rating": {"required": True}}


    def create(self, validated_data):
        """Create with serializer"""
        req_user = self.context["request"].user
        recipe = validated_data.pop("recipe",None)
        if recipe:
            comment = RecipeComment.objects.create(user=req_user, recipe=recipe, **validated_data)
            return comment
        else:
            raise serializers.ValidationError("Recipe is required to create a comment")


class RecipeSQLDetailSerializer(RecipeSerialzier):
    """Serializer for recipe detail !"""
    top_five_comments = serializers.SerializerMethodField()
    steps = RecipeStepSerialzier(many=True, required=False)
    class Meta(RecipeSerialzier.Meta):
        fields = RecipeSerialzier.Meta.fields + ['steps','create_time','likes','save_count','views','top_five_comments']
        read_only_fields = RecipeSerialzier.Meta.read_only_fields + ['likes','save_count','views','top_five_comments']

    def get_top_five_comments(self, obj):
        try:
            comments = obj.recipe_comment.order_by('-created_time')[:5]
            data = RecipeCommentSerializer(comments, many=True).data
            return data
        except Exception as e:
            print(e, "get_top_five_comments")
class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification"""
    class Meta:
        model = Notification
        fields = ['id', 'title', 'read','message', 'created', 'delievered']
        read_only_fields = ['id',  'message', 'title', 'read', 'created','delievered' ]


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