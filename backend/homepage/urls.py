from django.urls import path
from .views import (
    CurrentHomepageConfigView, UpdateHomepageConfigView,
    BentoFacilityListView, BentoFacilityCreateView, BentoFacilityDetailView,
    GalleryListView, GalleryCreateView, GalleryDetailView, GoogleMapsReviewsView
)

urlpatterns = [
    # CMS Core Config URLs
    path('config/current/', CurrentHomepageConfigView.as_view(), name='current-homepage-config'),
    path('config/update/', UpdateHomepageConfigView.as_view(), name='update-homepage-config'),
    
    # Dynamic Bento Grid Layout URLs
    path('bento/', BentoFacilityListView.as_view(), name='bento-list'),
    path('bento/create/', BentoFacilityCreateView.as_view(), name='bento-create'),
    path('bento/<int:pk>/', BentoFacilityDetailView.as_view(), name='bento-detail'),
    
    # Dynamic Gallery & Event (with Title) URLs
    path('gallery/', GalleryListView.as_view(), name='gallery-list'),
    path('gallery/create/', GalleryCreateView.as_view(), name='gallery-create'),
    path('gallery/<int:pk>/', GalleryDetailView.as_view(), name='gallery-detail'),
    path('reviews/maps/', GoogleMapsReviewsView.as_view(), name='google-reviews'),
]