from __future__ import print_function, unicode_literals, absolute_import, division

import six
import peewee

from ._filterops import OP
from .exceptions import UnknownFilterOperator


class Filter(object):
    """
    Basic Filter class.

    This filter instance requires being bound to a valid model field
    (maybe with a custom accessor), and has a pre-configured *operator*,
    which will be used to build query expression against a given value.

    :param field_name: specify the model field the current filter operates on.
    :param accessor: a spec for get a computed field, e.g.
        `:x.y` for accessing `Compound.extra_data['x']['y']`
    :param type: subclass of peewee.Field, specifies the type of computed field,
        e.g. `IntegerField` indicates `Compound.extra_data['x']['y']` is of int
        type.
    :param operator: specify a supported lookup operators
        (listed in peewee_filters.OP)

    For all available methods&operators, see
    http://docs.peewee-orm.com/en/latest/peewee/querying.html#query-operators
    """

    def __init__(self, field_name=None,
                 accessor=None, type=None,
                 model=None,
                 operator=OP.EQ,
                 **kwargs):
        self._model = model  # explicitly set if from foreign model
        self.field_name = field_name
        self._accessor = accessor
        self.field_type = type
        try:
            self.operator = getattr(OP, operator) if isinstance(operator, six.text_type) else operator
        except AttributeError:
            raise UnknownFilterOperator(operator)
        self.kwargs = kwargs

    def __repr__(self):
        return '<{}(on="{}")>'.format(self.__class__.__name__, self.field_name)

    @property
    def model(self):
        return self._model or self.parent._meta.model

    @property
    def field(self):
        """Return the model field, or an expression represnting a computed field"""

        _field = self.model._meta.fields.get(self.field_name, None)

        if isinstance(self._accessor, six.text_type):
            spec = self._accessor
            if spec[0] == ':':
                key_paths = spec[1:].split('.')
                # can be used to access nested JSONField
                for p in key_paths:
                    try:
                        p = int(p)
                    except ValueError:
                        pass
                    _field = _field[p]
        elif callable(self._accessor):
            _field = self._accessor(_field)

        ctx = self.model._meta.database.get_sql_context()
        if self.field_type:
            _field = _field.cast(self.field_type().ddl_datatype(ctx).sql)

        return _field

    def as_expr(self, arg):
        if not self.field:
            raise RuntimeError(
                'The basic Filter requires being bound to a valid model field. '
                'If you have custom logic that operates on multiple fields, '
                'make a subclass and write your logic in as_expr method.'
            )

        bound_operator = self.operator(self.field)
        return bound_operator.as_expr(arg)

    def post_filter(self, results, arg):
        return results


class FilterPack(dict):
    pass


def _accessor_as_filter_name(spec):
    if not spec:
        return None

    if isinstance(spec, six.text_type):
        return spec.replace('.', '__').lstrip(':')


def _operator_as_filter_name(op):
    if not op:
        return None

    if isinstance(op, type) and issubclass(op, OP):
        return op.name.lower()

    return op.lower()


def filter_pack(spec):
    filters = FilterPack()

    for field_name, accessors in spec.items():
        for accessor, accessor_pack in accessors.items():
            for operator in accessor_pack['operators']:
                filter_name = '__'.join(x for x in [
                    field_name,
                    _accessor_as_filter_name(accessor),
                    _operator_as_filter_name(operator)
                ] if x)
                filters[filter_name] = Filter(
                    field_name=field_name,
                    accessor=accessor,
                    type=accessor_pack['type'],
                    operator=operator,
                    **accessor_pack.get('kwargs', {})
                )
    return filters
