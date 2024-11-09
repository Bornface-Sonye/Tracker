# Generated by Django 4.2.7 on 2024-11-09 01:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0005_remove_complaint_response_alter_complaint_unit_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='response',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='No', help_text='Indicate if the complaint has been responded to', max_length=3),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='unit_code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='complaints.unitcourse'),
        ),
        migrations.AlterField(
            model_name='response',
            name='complaint_code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='complaints.complaint'),
        ),
        migrations.AlterField(
            model_name='response',
            name='unit_code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='complaints.unitcourse'),
        ),
    ]