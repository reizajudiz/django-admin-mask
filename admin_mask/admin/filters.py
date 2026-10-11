from django.contrib.admin import ListFilter
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class BlankFilter(ListFilter):
    parameter_name = None
    template = 'admin/blank_filter.html'

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                f'The list filter "{self.__class__.__name__}" does not specify '
                'a "parameter_name".' % self.__class__.__name__
            )

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

    def value(self):
        return self.used_parameters.get(self.parameter_name, None)

    def has_output(self):
        return True

    def expected_parameters(self):
        return [self.parameter_name]

    def choices(self, cl):
        return []


def qs_remove_filter(lookup, queryset):
    """
    Remove filter lookup in queryset
    """
    query = queryset.query
    # queryset.model._meta.get_field(lookup).__class__
    q = Q(**{lookup: None})
    clause, _ = query._add_q(q, query.used_aliases)

    def filter_lookups(child):
        try:
            return child.lhs.target != clause.children[0].lhs.target
        except Exception:
            try:
                return child.lhs.lhs.target != clause.children[0].lhs.target
            except Exception:
                return True

    query.where.children = list(filter(filter_lookups, query.where.children))
