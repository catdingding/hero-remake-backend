from rest_framework import serializers
import serpy

from base.serializers import BaseModelSerializer, SerpyModelSerializer

from asset.models import Image


class ImageSerializer(SerpyModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'name', 'path']
