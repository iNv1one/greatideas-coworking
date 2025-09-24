# Generated migration for staff notification fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),  # Замените на последнюю миграцию
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='staff_notification_sent',
            field=models.BooleanField(default=False, verbose_name='Уведомление персонала отправлено'),
        ),
        migrations.AddField(
            model_name='order',
            name='staff_message_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='ID сообщения в чате персонала'),
        ),
    ]