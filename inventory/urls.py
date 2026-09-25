from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, ItemViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("tags", TagViewSet)
router.register("items", ItemViewSet)

urlpatterns = router.urls