# Generated by Django 5.2 on 2025-07-26 23:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('black_invoices', '0002_pagoventa_metodo_pago_pagoventa_referencia_pago_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TasaCambio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha')),
                ('tasa_usd_ves', models.DecimalField(decimal_places=2, help_text='Bolívares por cada dólar', max_digits=10, verbose_name='Tasa USD a VES')),
                ('activa', models.BooleanField(default=True, verbose_name='Tasa Activa')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
            ],
            options={
                'verbose_name': 'Tasa de Cambio',
                'verbose_name_plural': 'Tasas de Cambio',
                'ordering': ['-fecha', '-fecha_creacion'],
            },
        ),
        migrations.RemoveField(
            model_name='pagoventa',
            name='referencia_pago',
        ),
        migrations.AddField(
            model_name='pagoventa',
            name='referencia',
            field=models.CharField(blank=True, help_text='Número de referencia, confirmación o voucher', max_length=50, null=True, verbose_name='Referencia/Número'),
        ),
    ]
