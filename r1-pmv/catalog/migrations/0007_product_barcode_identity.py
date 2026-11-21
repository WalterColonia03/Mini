"""Preserve existing identifiers as unclassified literal scanner keys."""
import unicodedata

import django.db.models.deletion
from django.db import migrations, models


def reserve_existing_literals(apps, schema_editor):
    alias = schema_editor.connection.alias
    Product = apps.get_model("catalog", "Product")
    Key = apps.get_model("catalog", "ProductBarcodeKey")
    claims, seen = [], {}
    for pk, code in Product.objects.using(alias).values_list("pk", "barcode").iterator():
        key = "".join(unicodedata.normalize("NFKC", code or "").split()).casefold()
        if not key or len(key) > 64:
            raise RuntimeError(f"Product {pk}: invalid literal key; review before retrying migration.")
        if key in seen:
            raise RuntimeError(f"Barcode key collision: {seen[key]} and {pk}; review without merging products.")
        seen[key] = pk
        claims.append(Key(product_id=pk, reading_key=key))
    Key.objects.using(alias).bulk_create(claims)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_category_state_version")]
    operations = [
        migrations.AddField(
            model_name="product", name="barcode_type",
            field=models.CharField(max_length=12, default="UNCLASSIFIED", choices=[
                ("UNCLASSIFIED", "Sin clasificar (registro anterior)"),
                ("INTERNAL", "Código interno"), ("GTIN", "GTIN del fabricante"),
            ]),
        ),
        migrations.AddConstraint(model_name="product", constraint=models.CheckConstraint(
            condition=models.Q(barcode_type__in=["UNCLASSIFIED", "INTERNAL", "GTIN"]),
            name="product_barcode_type_valid",
        )),
        migrations.CreateModel(name="ProductBarcodeKey", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("reading_key", models.CharField(max_length=64, unique=True)),
            ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                related_name="barcode_keys", to="catalog.product")),
        ], options={"ordering": ["reading_key"]}),
        migrations.RunPython(reserve_existing_literals, migrations.RunPython.noop),
    ]
