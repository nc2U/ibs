export interface LabelSpec {
  code: string
  name: string
  columns: number
  rows: number
  perPage: number
  labelWidth: string
  labelHeight: string
  marginTop: string
  marginLeft: string
  gapX: string
  gapY: string
}

export interface PrintOptions {
  specCode: '3107' | '3108' | '3105'
  startOffset: number // 1-based start cell index
  honorific: '귀하' | '님' | '앞' | ''
  showUnitInfo: boolean
  addressType: 'auto' | 'dm' | 'id' // auto: 수령지 우선, dm: 우편송부지, id: 주민등록지
  fontSize: 'sm' | 'base' | 'lg'
}

export const SPECS: Record<string, LabelSpec> = {
  '3107': {
    code: '3107',
    name: 'Formtec 3107 (16칸 / 2열×8행, 99.1×34mm)',
    columns: 2,
    rows: 8,
    perPage: 16,
    labelWidth: '99.1mm',
    labelHeight: '34mm',
    marginTop: '12mm',
    marginLeft: '4mm',
    gapX: '3.8mm',
    gapY: '0mm',
  },
  '3108': {
    code: '3108',
    name: 'Formtec 3108 (14칸 / 2열×7행, 99.1×38.1mm)',
    columns: 2,
    rows: 7,
    perPage: 14,
    labelWidth: '99.1mm',
    labelHeight: '38.1mm',
    marginTop: '15.15mm',
    marginLeft: '4mm',
    gapX: '3.8mm',
    gapY: '0mm',
  },
  '3105': {
    code: '3105',
    name: 'Formtec 3105 (21칸 / 3열×7행, 63.5×38.1mm)',
    columns: 3,
    rows: 7,
    perPage: 21,
    labelWidth: '63.5mm',
    labelHeight: '38.1mm',
    marginTop: '15.15mm',
    marginLeft: '7.25mm',
    gapX: '2.5mm',
    gapY: '0mm',
  },
}
