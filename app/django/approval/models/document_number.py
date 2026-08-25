from django.db import models, transaction


class DocNumberSequence(models.Model):
    """
    문서 유형별 연도별 채번 시퀀스 테이블.

    select_for_update()를 통해 동시 승인 시 채번 레이스컨디션(Race Condition)을 방지합니다.
    """

    doc_type = models.ForeignKey(
        'approval.DocumentType',
        on_delete=models.CASCADE,
        related_name='number_sequences',
        verbose_name='문서 유형',
    )
    year = models.PositiveSmallIntegerField('연도')
    last_number = models.PositiveIntegerField('마지막 채번', default=0)

    class Meta:
        unique_together = ('doc_type', 'year')
        verbose_name = '08. 문서 채번 시퀀스'
        verbose_name_plural = '08. 문서 채번 시퀀스 목록'

    def __str__(self):
        return f'{self.doc_type.code}-{self.year}: {self.last_number:04d}'

    @classmethod
    def next_number(cls, doc_type, year: int) -> int:
        """
        원자적(atomic) 채번: 동일 doc_type + year에 대해 select_for_update로 행 잠금 후
        last_number를 1 증가시켜 반환합니다.

        Usage:
            seq = DocNumberSequence.next_number(doc_type, 2026)
            doc_number = f'{doc_type.code}-2026-{seq:04d}'
        """
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
                doc_type=doc_type,
                year=year,
                defaults={'last_number': 0},
            )
            obj.last_number += 1
            obj.save(update_fields=['last_number'])
            return obj.last_number
