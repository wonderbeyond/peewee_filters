from collections import Container

import six
import peewee
from playhouse.postgres_ext import ArrayField, JSONField

from .exceptions import InvalidFilterOperatorArgument


__all__ = ['OP']


class _OPMcs(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(_OPMcs, cls).__new__(cls, name, bases, attrs)
        new_class.name = name
        if name != 'OP':
            # For you can see `OP.EQ` etc.
            OP = globals()['OP']
            setattr(OP, name, new_class)
        return new_class


class OP(six.with_metaclass(_OPMcs)):
    """
    Base class representing a filter operator.

    A filter operator instance is bound to a field(or expression) as the its
    left-hand side, can build the query expression against a given value.
    """

    def __init__(self, field):
        self.field = field

    def as_expr(self, arg):
        raise NotImplemented


class EQ(OP):
    def as_expr(self, arg):
        return self.field == arg


class LT(OP):
    def as_expr(self, arg):
        return self.field < arg


class LTE(OP):
    def as_expr(self, arg):
        return self.field <= arg


class GT(OP):
    def as_expr(self, arg):
        return self.field > arg


class GTE(OP):
    def as_expr(self, arg):
        return self.field >= arg


class NE(OP):
    def as_expr(self, arg):
        return self.field != arg


class IN(OP):
    def as_expr(self, arg):
        return self.field.in_(arg)


class NOT_IN(OP):
    def as_expr(self, arg):
        return self.field.not_in(arg)


class IS_NULL(OP):
    def as_expr(self, arg):
        is_null = self.field.is_null()
        return is_null if arg else (~is_null)


class LIKE(OP):
    def as_expr(self, arg):
        return self.field % arg


class ILIKE(OP):
    def as_expr(self, arg):
        return self.field ** arg


class BETWEEN(OP):
    def as_expr(self, arg):
        if not isinstance(arg, Container) or not len(arg) == 2:
            raise InvalidFilterOperatorArgument(
                'BETWEEN operator only accepts a 2-element tuple')
        return self.field.between(*arg)


class REGEXP(OP):
    def as_expr(self, arg):
        return self.field.regexp(arg)


class IREGEXP(OP):
    def as_expr(self, arg):
        return self.field.iregexp(arg)


class CONTAINS(OP):
    def as_expr(self, arg):
        if isinstance(self.field, ArrayField):
            return self.field.contains(*arg)
        elif isinstance(self.field, JSONField):
            return self.field.contains(arg)
        # or for substring
        return peewee.Expression(self.field, peewee.OP.LIKE, '%{0}%'.format(arg))


class ICONTAINS(OP):
    def as_expr(self, arg):
        if isinstance(self.field, ArrayField):
            return self.field.contains(*arg)
        # or for substring
        return peewee.Expression(self.field, peewee.OP.ILIKE, '%{0}%'.format(arg))


class STARTSWITH(OP):
    def as_expr(self, arg):
        return peewee.Expression(self.field, peewee.OP.LIKE, '{0}%'.format(arg))


class ISTARTSWITH(OP):
    def as_expr(self, arg):
        return peewee.Expression(self.field, peewee.OP.ILIKE, '{0}%'.format(arg))


class ENDSWITH(OP):
    def as_expr(self, arg):
        return peewee.Expression(self.field, peewee.OP.LIKE, '%{0}'.format(arg))


class IENDSWITH(OP):
    def as_expr(self, arg):
        return peewee.Expression(self.field, peewee.OP.ILIKE, '%{0}'.format(arg))
