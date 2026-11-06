from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('inventory', '0007_retirement_workflow')]

    operations = [migrations.CreateModel(
        name='LoginAttempt',
        fields=[
            ('key', models.CharField(max_length=64, primary_key=True, serialize=False)),
            ('failures', models.PositiveSmallIntegerField(default=0)),
            ('window_started', models.DateTimeField(db_index=True)),
        ],
    )]
