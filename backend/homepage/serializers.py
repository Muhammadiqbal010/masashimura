from rest_framework import serializers
from .models import HomepageConfig, BentoFacility, GalleryLookbook

class HomepageConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomepageConfig
        fields = '__all__'

class BentoFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BentoFacility
        fields = '__all__'

class GalleryLookbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryLookbook
        fields = '__all__'