from rest_framework import serializers
from .models import Category, Tag, Item

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

class ItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="name", queryset=Category.objects.all(),
        allow_null=True, required=False,
    )
    tags = serializers.SlugRelatedField(
        slug_field="name", queryset=Tag.objects.all(),
        many=True, required=False,
    )
    class Meta:
        model = Item
        fields = "__all__"