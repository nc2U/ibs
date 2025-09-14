from django.db import models


class UnitType(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트', related_name='types')
    SORT_CHOICES = (('1', '공동주택'), ('2', '오피스텔'), ('3', '숙박시설'),
                    ('4', '지식산업센터'), ('5', '근린생활시설'), ('6', '기타'))
    sort = models.CharField('타입종류', max_length=1, choices=SORT_CHOICES)
    name = models.CharField('타입명칭', max_length=10, db_index=True)
    color = models.CharField('타입색상', max_length=20)
    actual_area = models.DecimalField('전용면적(㎡)', max_digits=7, decimal_places=4, null=True, blank=True)
    supply_area = models.DecimalField('공급면적(㎡)', max_digits=7, decimal_places=4, null=True, blank=True)
    contract_area = models.DecimalField('계약면적(㎡)', max_digits=7, decimal_places=4, null=True, blank=True)
    average_price = models.PositiveBigIntegerField('평균가격', null=True, blank=True)
    PRICE_SET_CHOICES = (('1', '타입별 설정'), ('2', '층타입별 설정'), ('3', '호별 설정'))
    price_setting = models.CharField('공급가 설정 옵션', max_length=1, choices=PRICE_SET_CHOICES, default='2')
    num_unit = models.PositiveSmallIntegerField('세대수')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '01. 타입 정보'
        verbose_name_plural = '01. 타입 정보'


class UnitFloorType(models.Model):  # 층별 타입
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트', related_name='floors')
    sort = models.CharField('타입종류', max_length=1, choices=UnitType.SORT_CHOICES)
    start_floor = models.SmallIntegerField('시작 층')
    end_floor = models.SmallIntegerField('종료 층')
    extra_cond = models.CharField('방향/위치', max_length=20, blank=True,
                                  help_text='동일범위의 층범위를 방향/위치 등으로 구분해야 할 필요가 있는 경우 입력')
    alias_name = models.CharField('층별 범위 명칭', max_length=20, db_index=True)

    def __str__(self):
        return self.alias_name

    class Meta:
        ordering = ['-project', 'sort', '-end_floor']
        verbose_name = '02. 층별 조건'
        verbose_name_plural = '02. 층별 조건'


class KeyUnit(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트', related_name='units')
    sort = models.CharField('종류', max_length=1, choices=(('1', '메인유닛'), ('2', '부대시설')), default='1')
    unit_type = models.ForeignKey(UnitType, on_delete=models.PROTECT, verbose_name='타입')
    unit_code = models.CharField('코드번호', max_length=8, db_index=True)

    def __str__(self):
        return f'{self.unit_code}'

    class Meta:
        ordering = ['id', '-project']
        verbose_name = '03. 계약 유닛'
        verbose_name_plural = '03. 계약 유닛'


class BuildingUnit(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.PROTECT, verbose_name='프로젝트')
    name = models.CharField('동(건물)이름', max_length=10, db_index=True)

    class Meta:
        ordering = ('-project', 'id')
        verbose_name = '04. 동수'
        verbose_name_plural = '04. 동수'

    def __str__(self):
        return self.name


class HouseUnit(models.Model):
    unit_type = models.ForeignKey(UnitType, on_delete=models.PROTECT, verbose_name='타입')
    floor_type = models.ForeignKey(UnitFloorType, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='층범위 타입')
    building_unit = models.ForeignKey(BuildingUnit, on_delete=models.PROTECT, verbose_name='동수')
    name = models.CharField('호수', max_length=5, blank=True, db_index=True)
    key_unit = models.OneToOneField(KeyUnit, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='계약유닛')
    bldg_line = models.PositiveSmallIntegerField('라인')
    floor_no = models.SmallIntegerField('층수')
    is_hold = models.BooleanField('홀딩 여부', default=False)
    hold_reason = models.CharField('홀딩 사유', max_length=100, blank=True)

    def __str__(self):
        return f'{self.building_unit}-{self.name}'

    class Meta:
        ordering = ['-building_unit__project', 'building_unit', '-floor_no', 'bldg_line']
        verbose_name = '05. 호수'
        verbose_name_plural = '05. 호수'


class OptionItem(models.Model):
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, verbose_name='프로젝트')
    types = models.ManyToManyField('UnitType', verbose_name='타입구분')
    opt_code = models.CharField('품목코드', max_length=20, blank=True, null=True)
    opt_name = models.CharField('품목이름', max_length=100, db_index=True)
    opt_desc = models.CharField('세부옵션', max_length=200, blank=True, null=True)
    opt_maker = models.CharField('제조사', max_length=20, blank=True, null=True)
    opt_price = models.PositiveIntegerField(verbose_name='옵션가격')
    opt_deposit = models.PositiveIntegerField('계약금', null=True, blank=True)
    opt_balance = models.PositiveIntegerField('잔금', null=True, blank=True)

    def __str__(self):
        return self.opt_name

    class Meta:
        verbose_name = '06. 옵션 품목'
        verbose_name_plural = '06. 옵션 품목'
