from __future__ import print_function, unicode_literals, absolute_import, division

import copy
from collections import OrderedDict

from six import with_metaclass

from .filters import Filter, FilterPack
from .exceptions import UnknownFilter


class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.filter_overrides = getattr(options, 'filter_overrides', {})


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['declared_filters'] = cls.get_declared_filters(bases, attrs)

        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)
        new_class._meta = FilterSetOptions(getattr(new_class, 'Meta', None))

        # base_filters is filter on class, not instance
        new_class.base_filters = new_class.get_filters()
        for filter_ in new_class.base_filters.values():
            # filter_.model = new_class._meta.model
            filter_.parent = new_class

        return new_class

    @classmethod
    def get_declared_filters(cls, bases, attrs):
        filters = []

        for name, obj in list(attrs.items()):
            if isinstance(obj, Filter):
                filters.append([name, attrs.pop(name)])
            elif isinstance(obj, FilterPack):
                filters.extend([k, v] for k, v in obj.items())
                attrs.pop(name)

        # Default the `filter.field_name` to the attribute name on the filterset
        for filter_name, f in filters:
            if getattr(f, 'field_name', None) is None:
                f.field_name = filter_name.split('__')[0]

        # merge declared filters from base classes
        for base in reversed(bases):
            if hasattr(base, 'declared_filters'):
                filters = [
                    (name, f) for name, f
                    in base.declared_filters.items()
                    if name not in attrs
                ] + filters

        return OrderedDict(filters)


FILTER_FOR_DBFIELD_DEFAULTS = {}


class BaseFilterSet(object):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS
    FILTER_MODIFIERS = {'~'}

    def __init__(self, data=None):
        self.is_bound = data is not None
        self.data = data or {}

        # make an instance-level copy
        self.filters = copy.deepcopy(self.base_filters)

    @classmethod
    def get_filters(cls):
        """
        Get all filters for the filterset. This is the combination of declared and
        generated filters.

        Please access `FilterSet.base_filters` instead.
        """
        filters = cls.declared_filters.copy()

        # No model specified - skip filter generation
        if not cls._meta.model:
            return filters

        return filters

    @property
    def applied_filters(self):
        if not self.is_bound:
            raise RuntimeError('unbound filterset')

        def _strip_modifiers(k):
            # '~qml_count__between' => 'qml_count__between'
            for m in self.FILTER_MODIFIERS:
                if k.startswith(m):
                    return k[len(m):]
            return k

        res = []
        for k, arg in self.data.items():
            if k.startswith('#'):
                continue
            negated = k.startswith('~')

            fk = _strip_modifiers(k)

            if fk not in self.filters:
                raise UnknownFilter('The filter key `{}` is unknown.'.format(fk))

            if fk in self.filters:
                # res[k] = self.filters[fk]
                res.append(dict(
                    negated=negated,
                    filter=self.filters[fk],
                    name=fk,
                    arg=arg,
                ))
        return res

    @property
    def filtering_on_models(self):
        return set(f['filter'].model for f in self.applied_filters)

    def as_expr(self):
        if not self.is_bound:
            raise RuntimeError('Cannot call FilterSet.as_expr on unbound instance!')

        final_expr = None

        for af in self.applied_filters:
            filter = af['filter']
            negated = af['negated']
            arg = af['arg']

            expr = filter.as_expr(arg)

            if expr is None:
                continue

            if negated:
                expr = ~expr

            if final_expr is None:
                final_expr = expr
            else:
                final_expr &= expr

        return final_expr


class FilterSet(with_metaclass(FilterSetMetaclass, BaseFilterSet)):
    pass
