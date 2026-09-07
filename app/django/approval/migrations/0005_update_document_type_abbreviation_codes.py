from django.db import migrations

CODE_MAPPING = {
    'OFFICIAL_LETTER': 'OL',
    'GENERAL': 'GP',
    'LEAVE': 'LV',
    'BUSINESS_TRIP': 'BT',
    'OVERTIME': 'OT',
    'HR_APPOINTMENT': 'HR',
    'HR_REQUEST': 'RQ',
    'PURCHASE': 'PO',
    'EXPENSE': 'ER',
    'EXPENSE_SETTLEMENT': 'ES',
    'ADVANCE': 'AP',
    'CONTRACT': 'CT',
    'CONTRACT_CHANGE': 'CC',
    'LEGAL_REVIEW': 'LR',
    'BUSINESS_REVIEW': 'BR',
    'BUSINESS_APPROVAL': 'BA',
    'PROJECT_DECISION': 'PD',
}

REVERSE_CODE_MAPPING = {v: k for k, v in CODE_MAPPING.items()}


def update_codes_forward(apps, schema_editor):
    DocumentType = apps.get_model('approval', 'DocumentType')
    for old_code, new_code in CODE_MAPPING.items():
        doc_type = DocumentType.objects.filter(code=old_code).first()
        if doc_type:
            doc_type.code = new_code
            if new_code == 'GP' and not doc_type.form_template_key:
                doc_type.form_template_key = 'GENERAL'
            doc_type.save(update_fields=['code', 'form_template_key'])


def update_codes_backward(apps, schema_editor):
    DocumentType = apps.get_model('approval', 'DocumentType')
    for new_code, old_code in REVERSE_CODE_MAPPING.items():
        doc_type = DocumentType.objects.filter(code=new_code).first()
        if doc_type:
            doc_type.code = old_code
            doc_type.save(update_fields=['code'])


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0004_standardize_form_template_choices'),
    ]

    operations = [
        migrations.RunPython(update_codes_forward, update_codes_backward),
    ]
