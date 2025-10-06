# Generated migration for CompletedEvent model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('startup_game', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_key', models.CharField(max_length=100, verbose_name='Ключ события')),
                ('choice_id', models.CharField(blank=True, max_length=100, verbose_name='ID выбранного варианта')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('game_day', models.IntegerField(verbose_name='День игры когда произошло событие')),
                ('event_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='startup_game.eventtemplate')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completed_events', to='startup_game.gamesession')),
            ],
            options={
                'verbose_name': 'Завершенное событие',
                'verbose_name_plural': 'Завершенные события',
                'ordering': ['-completed_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='completedevent',
            constraint=models.UniqueConstraint(fields=('session', 'event_key'), name='unique_event_per_session'),
        ),
    ]