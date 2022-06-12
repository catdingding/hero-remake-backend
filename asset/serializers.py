from rest_framework import serializers
import serpy

from base.serializers import BaseModelSerializer, SerpyModelSerializer

from asset.models import Image, Scene


class ImageSerializer(SerpyModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'name', 'path']


class SceneSerializer(SerpyModelSerializer):
    class Meta:
        model = Scene
        fields = ['id', 'name', 'description', 'contents']
