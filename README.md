Peewee Filters
==============

Generating peewee query expression against json payload.
Like [Django Filter](https://github.com/carltongibson/django-filter) but works with [peewee](https://github.com/coleifer/peewee).


```
pip install peewee_filters
```


```python
from xxx.models import Book
from peewee_filters import FilterSet, Filter, OP


class BookFilter(FilterSet):
    category__in = Filter('category', operator='IN')
    tags__contains = Filter('tags', operator='CONTAINS')

    class Meta:
        model = Book


f = BookFilter({
    'category__in': ['Programming'],
    'tags__contains': ['Python', 'Postgresql'],
    '~tags__contains': ['Jupyter']
})

expr = f.as_expr()

# Inspect the SQL:
sql_str = db.cursor().mogrify(*Book.select().where(expr).sql()).decode()
print(sql_str)
```

**Output:**

```sql
SELECT "t1"."id",
       "t1"."title",
       "t1"."description",
       "t1"."category",
       "t1"."tags",
FROM "book" AS "t1" WHERE (
    (("t1"."category" IN ('Programming')) AND ("t1"."tags" @> ARRAY['Python','Postgresql']::VARCHAR(255)[]))
    AND NOT ("t1"."tags" @> ARRAY['Jupyter']::VARCHAR(255)[]))
```
