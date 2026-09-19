from django.db import migrations


def add_inbound_report_doctype(apps, schema_editor):
    DocCategory = apps.get_model('approval', 'DocCategory')
    DocumentType = apps.get_model('approval', 'DocumentType')

    common_cat = DocCategory.objects.filter(code='COMMON').first()
    DocumentType.objects.get_or_create(
        code='IR',
        defaults={
            'category': common_cat,
            'name': '수신 공문 처리 보고',
            'form_template_key': 'INBOUND_REPORT',
            'default_security_level': '2',
            'route_type': 'organization',
            'description': '접수된 대외/관공서 공문의 내부 보고, 대응 방안 및 회신 품의',
            'is_active': True,
        }
    )


def remove_inbound_report_doctype(apps, schema_editor):
    DocumentType = apps.get_model('approval', 'DocumentType')
    DocumentType.objects.filter(code='IR').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0003_approvaldocument_related_inbound_letter_and_more'),
    ]

    operations = [
        migrations.RunPython(add_inbound_report_doctype, reverse_code=remove_inbound_report_doctype),
    ]
