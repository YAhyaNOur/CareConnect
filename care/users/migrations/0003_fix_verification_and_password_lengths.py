from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_medecin_latitude_medecin_longitude_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient_insc",
            name="verification_code",
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name="psy_insc",
            name="verification_code",
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AlterField(
            model_name="patient_insc",
            name="my_password",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="patient_insc",
            name="passw",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="psy_insc",
            name="password",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="psy_insc",
            name="passw",
            field=models.CharField(max_length=128),
        ),
    ]
