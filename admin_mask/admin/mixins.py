# ruff: noqa: I001
from typing import ClassVar
from datetime import datetime, timedelta

from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .filters import BlankFilter, qs_remove_filter


class MaskDateFilter(BlankFilter):
    title = 'Date Filter'
    parameter_name = 'mask_date'

    def queryset(self, request, qs):
        return qs.all()


class MaskDateFilterMixin:
    mask_date_field = None
    filtering: ClassVar[dict] = {}

    def parse_mask_date_filter(self, request) -> dict:
        spt = request.GET.get('mask_date', None)
        if not spt:
            return {}

        ret = {}
        spt = [int(s) for s in spt.split('-')]
        if len(spt) == 3:
            ret = {
                'year': spt[0],
                'month': spt[1],
                'day': spt[2],
            }
        elif len(spt) == 2:
            ret = {
                'year': spt[0],
                'month': spt[1],
            }
        else:
            ret = {
                'year': spt[0],
            }
        return ret

    def get_mask_date_filter(self, request) -> tuple:
        spt = self.parse_mask_date_filter(request)
        if not spt:
            return None, None

        year = spt.get('year', None)
        month = spt.get('month', None)
        day = spt.get('day', None)
        if day:
            try:
                start = datetime(year, month, day, tzinfo=timezone.get_current_timezone())
            except Exception:
                return 'DAY ERROR', None
            until = start + timedelta(days=1)
        elif month:
            try:
                start = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
            except Exception:
                return 'MONTH ERROR', None
            # until is 1st next month
            until = start.replace(day=28) + timedelta(days=5)
            until = until.replace(day=1)
        else:
            try:
                start = datetime(year, 1, 1, tzinfo=timezone.get_current_timezone())
            except Exception as e:
                return 'YEAR ERROR', None
            # until is january 1st next year
            until = start.replace(year=start.year + 1)

        return None, {
            f'{self.mask_date_field}__gte': start,
            f'{self.mask_date_field}__lt': until,
        }

    def get_list_filter(self, req):
        ret = super().get_list_filter(req)
        if not ret:
            ret = []
        ret = list(ret)
        ret.append(MaskDateFilter)
        return tuple(ret)

    def get_queryset(self, req):
        qs = super().get_queryset(req)
        ret = self.mask_date_filter(req, qs)
        return ret

    def mask_date_filter(self, req, qs):
        if not self.mask_date_field:
            return qs

        err, spt = self.get_mask_date_filter(req)
        if not spt:
            return qs

        if err and err == 'DAY ERROR':
            messages.error(req, _('Filter date wrong parameter'))
            return qs
        elif err and err == 'MONTH ERROR':
            messages.error(req, _('Filter month wrong parameter'))
            return qs
        elif err and err == 'YEAR ERROR':
            messages.error(req, _('Filter year wrong parameter'))
            return qs

        self.filtering = spt
        ret = qs.filter(**self.filtering)
        return ret

    def changelist_view(self, req, extra_context=None):
        ec = {
            'mask_date_field': self.mask_date_field,
        }
        ret = super().changelist_view(req, extra_context=ec)
        if hasattr(ret, 'context_data') and 'cl' in ret.context_data:
            oqs = ret.context_data['cl'].queryset.all()
            for k in self.filtering:
                tk = k.replace('__gte', '').replace('__lt', '')
                qs_remove_filter(tk, oqs)
            ret.context_data['cl'].original_queryset = oqs
        return ret
