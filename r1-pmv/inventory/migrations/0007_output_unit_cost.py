from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inventory", "0006_lot_received_at_immutable")]
    operations = [
        migrations.AddField(
            model_name="stockwriteoff",
            name="unit_cost",
            field=models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="physicaladjustment",
            name="unit_cost",
            field=models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False),
        ),
    ]
