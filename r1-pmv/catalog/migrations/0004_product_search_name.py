import unicodedata

from django.db import migrations, models


def populate_search_names(apps, schema_editor):
    products = apps.get_model("catalog", "Product").objects.using(schema_editor.connection.alias)
    for product in products.only("pk", "name").iterator(chunk_size=500):
        key = unicodedata.normalize("NFC", product.name.casefold())
        products.filter(pk=product.pk).update(search_name=key)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_normalize_category_spaces")]
    operations = [
        migrations.AddField(
            model_name="product", name="search_name",
            field=models.TextField(editable=False, default=""), preserve_default=False,
        ),
        migrations.RunPython(populate_search_names, migrations.RunPython.noop),
    ]
