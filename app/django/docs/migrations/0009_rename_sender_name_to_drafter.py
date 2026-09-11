from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0008_officialletter_attachment_text_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='officialletter',
            old_name='sender_name',
            new_name='drafter_name',
        ),
        migrations.RenameField(
            model_name='officialletter',
            old_name='sender_position',
            new_name='drafter_position',
        ),
        migrations.RemoveField(
            model_name='officialletter',
            name='sender_department',
        ),
        migrations.AlterField(
            model_name='officialletter',
            name='drafter_name',
            field=models.CharField(max_length=50, verbose_name='기안/담당자명'),
        ),
        migrations.AlterField(
            model_name='officialletter',
            name='drafter_position',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='기안/담당 직위'),
        ),
    ]
