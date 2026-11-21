from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_product_name_and_minimum_policy")]
    operations = [migrations.AddField(
        model_name="category", name="state_version",
        field=models.PositiveBigIntegerField(default=0, editable=False),
    )]
