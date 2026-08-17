from rest_framework.routers import DefaultRouter
from .views import PromoViewSet

router = DefaultRouter()
router.register(r'promotions', PromoViewSet, basename='promotions')
urlpatterns = router.urls