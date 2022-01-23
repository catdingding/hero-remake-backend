from django.db import models
import serpy
import serpy.serializer
from serpy import Field

from rest_framework import serializers
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from chara.models import Chara


class ContextMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get('request')
        if self.request:
            self.user = self.request.user

            if hasattr(self.request, 'chara'):
                self.chara = self.request.chara
            if hasattr(self.request, 'country'):
                self.country = self.request.country
            if hasattr(self.request, 'team'):
                self.team = self.request.team


class TransferPermissionCheckerMixin:
    def validate(self, data):
        if not self.chara.has_transfer_permission:
            raise serializers.ValidationError("你不具有傳送權限")

        return super().validate(data)


class LockedEquipmentCheckMixin:
    def validate_item(self, item):
        if not item.type.is_transferable:
            raise serializers.ValidationError("此為綁定道具")
        if hasattr(item, 'equipment') and item.equipment.is_locked:
            raise serializers.ValidationError("此裝備已綁定")
        return item


class BaseSerializer(ContextMixin, FlexFieldsSerializerMixin, serializers.Serializer):
    pass


class BaseModelSerializer(ContextMixin, FlexFieldsSerializerMixin, serializers.ModelSerializer):
    pass


class SerpyModelSerializerMeta(serpy.serializer.SerializerMeta):
    @staticmethod
    def generate_model_fields(meta):
        output_fields = {}
        fields = getattr(meta, 'fields', None)
        exclude = getattr(meta, 'exclude', None)

        assert not (fields and exclude)
        assert not (fields is None and exclude is None)

        for field in meta.model._meta.concrete_model._meta.fields:
            if fields is not None:
                if fields != '__all__' and field.name not in fields:
                    continue
            else:
                if field.name in exclude:
                    continue

            if isinstance(field, models.ForeignKey):
                output_fields[field.name] = Field(attr=field.attname)
            else:
                output_fields[field.name] = Field()

        return output_fields

    def __new__(cls, name, bases, attrs):
        # Fields declared directly on the class.
        direct_fields = {}

        # Take all the Fields from the attributes.
        for attr_name, field in attrs.items():
            if isinstance(field, Field):
                direct_fields[attr_name] = field

        for k in direct_fields.keys():
            if k in attrs:
                del attrs[k]

        real_cls = super().__new__(cls, name, bases, attrs)

        field_map = cls._get_fields(direct_fields, real_cls)
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
            model_fields = cls.generate_model_fields(attrs['Meta'])
            model_fields.update(field_map)
            field_map = model_fields

        compiled_fields = cls._compile_fields(field_map, real_cls)

        real_cls._field_map = field_map
        real_cls._compiled_fields = tuple(compiled_fields)
        return real_cls


class SerpyModelSerializer(ContextMixin, serpy.Serializer, metaclass=SerpyModelSerializerMeta):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})

        fields = kwargs.pop('fields', [])
        omit = kwargs.pop('omit', [])

        self._options = {
            "fields": fields if len(fields) > 0 else self._get_query_param_value("fields"),
            "omit": omit if len(omit) > 0 else self._get_query_param_value("omit")
        }

        super().__init__(*args, **kwargs)

    def _serialize(self, instance, fields):
        if self._options['fields']:
            fields = [field for field in fields if field[0] in self._options['fields']]
        if self._options['omit']:
            fields = [field for field in fields if field[0] not in self._options['omit']]

        v = {}
        for name, getter, to_value, call, required, pass_self in fields:
            if pass_self:
                result = getter(self, instance)
            else:
                try:
                    result = getter(instance)
                except (KeyError, AttributeError):
                    if required:
                        raise
                    else:
                        continue
                if required or result is not None:
                    if call:
                        result = result()
                    if to_value:
                        result = to_value(result)
            v[name] = result

        return v

    def to_value(self, instance):
        if instance is None:
            return None

        fields = self._compiled_fields
        if self.many:
            serialize = self._serialize
            if hasattr(instance, 'all'):
                instance = instance.all()
            return [serialize(o, fields) for o in instance]
        return self._serialize(instance, fields)

    def default_getter(name):
        def getter(instance):
            return getattr(instance, name, None)
        return getter

    def _get_query_param_value(self, field):
        if not hasattr(self, "context") or not self.context.get("request"):
            return []

        values = self.context["request"].query_params.getlist(field)

        if not values:
            values = self.context["request"].query_params.getlist("{}[]".format(field))

        if values and len(values) == 1:
            return values[0].split(",")

        return values or []


class DateTimeField(serpy.Field):
    @staticmethod
    def to_value(value):
        return value.isoformat()[:-6] + 'Z'


class IdNameSerializer(SerpyModelSerializer):
    id = serpy.Field()
    name = serpy.Field()
