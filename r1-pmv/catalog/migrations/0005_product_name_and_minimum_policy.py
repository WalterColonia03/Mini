"""Preflight accepted product policies; never merge names or clamp minima."""
import unicodedata

import django.core.validators
from django.db import migrations, models


def prepare_product_keys(apps, schema_editor):
    products = apps.get_model("catalog", "Product").objects.using(schema_editor.connection.alias)
    rows = list(products.values_list("pk", "name", "search_name", "minimum_stock"))
    seen, changes = {}, []
    for pk, name, old_key, minimum in rows:
        key = unicodedata.normalize("NFC", " ".join(name.split()).casefold())
        if not key:
            raise RuntimeError(f"Product {pk}: empty normalized name; resolve before retrying migration.")
        if key in seen:
            raise RuntimeError(f"Product name collision: {seen[key]} and {pk}; resolve explicitly before retrying migration.")
        if minimum is None or not 0 <= minimum <= 999999:
            raise RuntimeError(f"Product {pk}: minimum outside 0..999999; resolve before retrying migration.")
        seen[key] = pk
        if old_key != key:
            changes.append((pk, key))
    for pk, key in changes:
        products.filter(pk=pk).update(search_name=key)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_product_search_name")]
    operations = [
        migrations.RunPython(prepare_product_keys, migrations.RunPython.noop),
        migrations.AlterField(model_name="product", name="search_name", field=models.TextField(editable=False, unique=True)),
        migrations.AlterField(model_name="product", name="minimum_stock", field=models.PositiveIntegerField(
            default=10, validators=[django.core.validators.MaxValueValidator(
                999999, message="Asegúrese de que este valor sea menor o igual a 999999.")],
        )),
        migrations.AddConstraint(model_name="product", constraint=models.CheckConstraint(
            condition=models.Q(minimum_stock__lte=999999), name="product_minimum_stock_lte_max")),
    ]
