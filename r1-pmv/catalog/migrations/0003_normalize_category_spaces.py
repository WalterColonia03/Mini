"""Normalize existing unique keys without renaming or merging business rows.

Collisions require an explicit operator decision. Abort before writing anything;
never merge/delete categories or change product references automatically.
"""
from django.db import migrations


def normalize_category_keys(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    alias = schema_editor.connection.alias
    rows = list(Category.objects.using(alias).values_list('pk', 'name', 'name_normalized'))
    seen = {}
    changes = []
    for pk, name, old_key in rows:
        key = ' '.join(name.split()).casefold()
        if not key or len(key) > 120:
            raise RuntimeError(f'Category {pk}: invalid normalized key; resolve before retrying migration.')
        if key in seen:
            raise RuntimeError(f'Category normalization collision: {seen[key]} and {pk}; resolve explicitly before retrying migration.')
        seen[key] = pk
        if old_key != key:
            changes.append((pk, key))
    for pk, key in changes:
        Category.objects.using(alias).filter(pk=pk).update(name_normalized=key)


class Migration(migrations.Migration):
    dependencies = [('catalog', '0002_product')]
    operations = [migrations.RunPython(normalize_category_keys, migrations.RunPython.noop)]
