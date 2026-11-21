from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('sales', '0004_saleline_product')]
    operations = [
        migrations.AddField(
            model_name='saleline', name='unit_cost',
            field=models.DecimalField(decimal_places=4, max_digits=14, null=True, editable=False),
        ),
    ]
