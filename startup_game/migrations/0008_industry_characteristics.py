# Generated migration for industry characteristics

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('startup_game', '0007_completedevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamesession',
            name='industry_competition',
            field=models.IntegerField(default=5, help_text='Уровень конкуренции (1-10)'),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='industry_regulatory_barriers',
            field=models.IntegerField(default=5, help_text='Регуляторные барьеры (1-10)'),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='industry_profitability',
            field=models.IntegerField(default=5, help_text='Прибыльность (1-10)'),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='industry_entry_cost',
            field=models.IntegerField(default=5, help_text='Стоимость входа (1-10)'),
        ),
        migrations.AddField(
            model_name='gamesession',
            name='industry_growth_potential',
            field=models.IntegerField(default=5, help_text='Потенциал роста (1-10)'),
        ),
    ]