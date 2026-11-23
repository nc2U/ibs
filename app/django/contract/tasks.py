from celery import shared_task

from contract.services import ContractorSensitiveService


@shared_task(name='contract.purge_expired_contractor_rrns')
def purge_expired_contractor_rrns_task():
    """보존기한(retention_until)이 도래한 계약자 고유식별정보(주민등록번호) 일괄 파기"""
    return ContractorSensitiveService.purge_expired_rrns()
