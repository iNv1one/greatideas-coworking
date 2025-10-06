# Generated manually on 2025-10-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('startup_game', '0008_industry_characteristics'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventtemplate',
            name='trigger_type',
            field=models.CharField(
                choices=[
                    ('sequential', 'Последовательное (по очереди)'),
                    ('random', 'Случайное (может появиться в любое время)'),
                    ('triggered', 'Инициируемое (появляется после выбора)'),
                ],
                default='sequential',
                help_text='Как срабатывает событие',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='eventtemplate',
            name='random_chance',
            field=models.FloatField(
                default=0.1,
                help_text='Вероятность появления каждый день (0.1 = 10%)'
            ),
        ),
        migrations.AddField(
            model_name='eventtemplate',
            name='min_day',
            field=models.IntegerField(
                default=1,
                help_text='Минимальный день для появления'
            ),
        ),
        migrations.AddField(
            model_name='eventtemplate',
            name='max_day',
            field=models.IntegerField(
                blank=True,
                help_text='Максимальный день (пусто = без ограничений)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='eventtemplate',
            name='parent_choices',
            field=models.TextField(
                blank=True,
                help_text='ID выборов, после которых появляется это событие (через запятую)'
            ),
        ),
        migrations.AddField(
            model_name='eventchoice',
            name='next_events',
            field=models.TextField(
                blank=True,
                help_text='Ключи событий, которые могут появиться после этого выбора (через запятую)'
            ),
        ),
        migrations.AddField(
            model_name='eventchoice',
            name='next_event_delay',
            field=models.IntegerField(
                default=1,
                help_text='Через сколько дней появится следующее событие'
            ),
        ),
    ]