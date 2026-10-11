from operator import attrgetter

from django import template
from django.utils import timezone

register = template.Library()


@register.filter()
def mask_date_available(qs, field):
    if qs is None:
        return 'NULL'

    if not qs.exists():
        return 'NULL'

    if '__' in field:
        field_obj = None
        field_model = qs.model
        for f in field.split('__'):
            field_obj = field_model._meta.get_field(f)
            fieldtype = field_obj.get_internal_type()
            field_model = getattr(field_obj, 'related_model', None)
    else:
        fieldtype = qs.model._meta.get_field(field).get_internal_type()

    if fieldtype == 'DateTimeField':
        cqs = qs.filter(**{field + '__isnull': False}).order_by(field)
        s = attrgetter(field.replace('__', '.'))(cqs[0])\
            .astimezone(timezone.get_current_timezone())
        u = attrgetter(field.replace('__', '.'))(cqs.latest(field))\
            .astimezone(timezone.get_current_timezone())
    else:
        # DATEFIELD no timezone
        cqs = qs.filter(**{field + '__isnull': False}).order_by(field)
        s = getattr(cqs[0], field)
        u = getattr(cqs.latest(field), field)

    s = s.strftime('%d-%m-%Y')
    u = u.strftime('%d-%m-%Y')
    return f'{s}:{u}'
