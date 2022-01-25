from django_filters import rest_framework as filters
from django.db.models import Q


class ItemFilter(filters.FilterSet):
    category = filters.NumberFilter(method='filter_common_field')
    element_type = filters.NumberFilter(method='filter_element_type')
    slot_type = filters.NumberFilter(method='filter_common_field')
    is_locked = filters.BooleanFilter(method='filter_is_locked')
    name_like = filters.CharFilter(method='filter_name_like')
    ordering = filters.ChoiceFilter(choices=[('name', 'name')], method='order_by')

    def get_field_name(self, name):
        if self.Meta.item_field is None:
            return name
        return '__'.join([self.Meta.item_field, name])

    def filter_common_field(self, queryset, name, value):
        return queryset.filter(**{self.get_field_name(f"type__{name}"): value})

    def filter_element_type(self, queryset, name, value):
        return queryset.filter(
            Q(**{self.get_field_name('equipment__element_type'): value}) |
            (
                ~Q(**{self.get_field_name('type__category'): 1}) &
                Q(**{self.get_field_name('type__element_type'): value})
            )
        )

    def filter_is_locked(self, queryset, name, value):
        condition = (
            Q(**{self.get_field_name('equipment__is_locked'): True}) |
            Q(**{self.get_field_name('type__is_transferable'): False})
        )
        if not value:
            condition = ~condition

        return queryset.filter(condition)

    def filter_name_like(self, queryset, name, value):
        return queryset.filter(
            Q(**{self.get_field_name('type__name') + '__contains': value}) |
            Q(**{self.get_field_name('equipment__custom_name') + '__contains': value})
        )

    def order_by(self, queryset, name, value):
        if value == 'name':
            queryset = queryset.order_by(self.get_field_name('type__name'))
        return queryset

    class Meta:
        item_field = None

    @classmethod
    def set_item_field(cls, field_name):
        class Filter(cls):
            class Meta:
                item_field = field_name

        return Filter
