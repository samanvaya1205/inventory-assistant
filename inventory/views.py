from django.shortcuts import render
from rest_framework import viewsets
from .models import Category, Tag, Item
from .serializers import CategorySerializer, TagSerializer, ItemSerializer
from .permissions import IsAdminRoleOrReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminRoleOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
