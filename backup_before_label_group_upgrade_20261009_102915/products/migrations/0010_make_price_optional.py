from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0009_product_product_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="price",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                blank=True,
                null=True,
            ),
        ),
    ]
