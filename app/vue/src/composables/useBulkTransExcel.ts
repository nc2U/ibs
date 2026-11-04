import { ref } from 'vue'
import ExcelJS from 'exceljs'
import {
  CODE_TO_EVIDENCE_MAP,
  EVIDENCE_TYPE_MAP,
  extractCellNumber,
  extractCellValue,
} from '@/composables/useExcelUpload'

/**
 * 다수 은행거래 + 회계 계정 대량 입력용 엑셀 템플릿 / 파서
 *
 * 지원 포맷:
 * 1. IBS 표준 템플릿: 그룹번호/분류금액 기반 다중 분할 지원
 * 2. 인터넷 뱅킹 원본 엑셀: 국민, 신한, 우리, 하나, 기업, 농협 등 주요 은행 다운로드 파일 자동 감지 및 변환
 * 3. 클립보드 TSV 복사-붙여넣기 지원
 */

interface Option {
  value: number | null | undefined
  label: string
}

export type BulkSystemType = 'project' | 'company'

export interface ExistingTransactionRef {
  deal_date?: string
  amount?: number | null
  sort?: number | null
  content?: string
}

export interface BulkParseOptions {
  bankAccounts: Option[]
  accounts: Array<{ value: number; label: string; is_cate_only?: boolean }>
  // 프로젝트: 계약자 후보 / 본사: 관계회사(프로젝트) 후보
  contracts: Array<{ value: number; label: string }>
  // 프로젝트 전용: 납부회차 후보
  payOrders?: Array<{ value: number; label: string }>
  systemType?: BulkSystemType
  targetBankAccount?: number | null // 사전 선택된 거래계좌 (있으면 일괄 적용)
  existingTransactions?: ExistingTransactionRef[] // 중복 거래 검사용
}

// 시스템별 '연관 대상' 열 이름 (프로젝트=계약자, 본사=관계회사(프로젝트))
export const relatedLabelOf = (t: BulkSystemType = 'project') =>
  t === 'project' ? '계약자' : '관계회사(프로젝트)'

// 1회 대량 입력 상한선 (브라우저 반응성 및 네트워크 안정성 보장)
export const MAX_BULK_ROWS = 250 // 최대 허용 엑셀 행 수
export const MAX_BULK_TRANSACTIONS = 60 // 최대 허용 은행거래 건수

export interface BulkEntry {
  rowNumber: number
  account: number | null
  account_name: string
  trader: string
  amount: number
  evidence_type: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  contract: number | null // 프로젝트: 계약자 ID / 본사: 관계회사(affiliate) ID
  contract_name: string
  installment_order?: number | null // 프로젝트: 납부회차 ID
  installment_order_name?: string
  isAutoMatched?: boolean // 규칙으로 자동 추천되었는지 여부
  isContractAutoMatched?: boolean
  errors: string[]
  warnings: string[]
}

export interface BulkTransaction {
  key: string
  firstRow: number
  bankForm: {
    deal_date: string
    bank_account: number | null | ''
    bank_account_name: string
    sort: 1 | 2
    amount: number | null
    content: string
    note: string
  }
  entries: BulkEntry[]
  entryTotal: number
  isBalanced: boolean
  isDuplicate?: boolean
  duplicateReason?: string
  errors: string[]
  warnings: string[]
  isValid: boolean
}

export interface BulkParseResult {
  fileFormat: 'ibs_template' | 'bank_raw'
  detectedBankName?: string
  transactions: BulkTransaction[]
  summary: {
    transactionCount: number
    validTransactions: number
    invalidTransactions: number
    entryCount: number
    duplicateCount: number
  }
  isValid: boolean
}

export const BULK_COLUMNS = [
  // 화면 폼(거래일자 → 메모 → 거래계좌 → 적요 → 입출금액 → 계정 → 계약자/관계회사 → 납부회차 → 거래처 → 분류금액 → 지출증빙)
  { header: '그룹번호', key: 'key', width: 12 },
  { header: '거래일자', key: 'deal_date', width: 14 },
  { header: '메모', key: 'note', width: 20 },
  { header: '거래계좌', key: 'bank_account', width: 22 },
  { header: '적요', key: 'content', width: 30 },
  { header: '구분(입금/출금)', key: 'sort', width: 16 },
  { header: '입출금액', key: 'amount', width: 16 },
  { header: '계정이름', key: 'account_name', width: 25 },
  { header: '__RELATED__', key: 'contract_name', width: 22 },
  { header: '납부회차', key: 'installment_order_name', width: 20 },
  { header: '거래처', key: 'trader', width: 25 },
  { header: '분류금액', key: 'entry_amount', width: 16 },
  { header: '지출증빙', key: 'evidence_type', width: 22 },
] as const

const SORT_MAP: Record<string, 1 | 2> = { 입금: 1, 출금: 2, '1': 1, '2': 2 }

// 엑셀 셀 값(Date/문자열/숫자)을 YYYY-MM-DD 로 정규화
const normalizeDate = (cell: ExcelJS.Cell | string): string => {
  if (typeof cell === 'string') {
    const s = cell.trim()
    const m = s.match(/^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})/)
    if (m) return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`
    const digits = s.replace(/[.\-/\s]/g, '')
    if (/^\d{8}/.test(digits)) {
      return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`
    }
    return s
  }
  const val = cell.value
  if (val instanceof Date) {
    const y = val.getUTCFullYear()
    const m = String(val.getUTCMonth() + 1).padStart(2, '0')
    const d = String(val.getUTCDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }
  const str = extractCellValue(cell).trim()
  const m = str.match(/^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})/)
  if (m) return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`
  const digits = str.replace(/[.\-/\s]/g, '')
  if (/^\d{8}/.test(digits)) {
    return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`
  }
  return str
}

const isValidDate = (s: string) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false
  const d = new Date(`${s}T00:00:00Z`)
  return !isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s
}

// ============================================
// 규칙 기반 계정과목 & 계약자 자동 매핑 엔진
// ============================================

interface KeywordCategoryRule {
  keywords: string[]
  accountKeywords: string[]
  sort?: 1 | 2 // 1: 입금 전용, 2: 출금 전용
}

const CATEGORY_RULES: KeywordCategoryRule[] = [
  // 이자수익 / 지급이자
  { keywords: ['이자', '결산이자', '예금이자'], accountKeywords: ['이자수익', '이자수입'], sort: 1 },
  { keywords: ['이자', '지급이자', '차입금이자', '대출이자'], accountKeywords: ['지급이자', '이자비용'], sort: 2 },
  // 지급수수료
  { keywords: ['수수료', '이체수수료', '펌뱅킹', '송금수수료', '타행이체', '발급수수료', '결제수수료', 'van', 'cms'], accountKeywords: ['수수료'] },
  // 식대 / 복리후생
  { keywords: ['식대', '점심', '식당', '도시락', '커피', '음료', '간식', '야식', '생수', '회식', '카페'], accountKeywords: ['복리후생', '식대'] },
  // 공과금 / 수도광열비
  { keywords: ['한전', '한국전력', '전기요금', '도시가스', '수도요금', '관리비', '난방비'], accountKeywords: ['수도광열', '공과금', '관리비'] },
  // 통신비
  { keywords: ['kt', 'skt', 'lgu', '케이티', '통신비', '인터넷', 'sk텔레콤', 'lg유플러스', '전화요금', '휴대폰'], accountKeywords: ['통신'] },
  // 여비교통비 / 차량유지비
  { keywords: ['주유', 'gs칼텍스', 'sk에너지', '에쓰오일', 's-oil', '현대오일', '하이패스', '주차', '톨게이트', 'ktx', '코레일', '택시', '세차'], accountKeywords: ['차량', '여비교통', '교통비'] },
  // 소모품비 / 도서인쇄비
  { keywords: ['소모품', '문구', '오피스', '다이소', '알파', '인쇄', '복사', '제본', '도서', '교보문고', '영풍문고'], accountKeywords: ['소모품', '도서'] },
  // 세금과공과
  { keywords: ['국세', '지방세', '취득세', '재산세', '등록면허세', '세무서', '구청', '원천세'], accountKeywords: ['세금과공과', '공과금'] },
  // 분양 수납 (프로젝트 입금)
  { keywords: ['계약금', '중도금', '잔금', '분양대금', '분양', '수납', '분담금', '부담금'], accountKeywords: ['분양수입', '분담금', '수입금'], sort: 1 },
]

/** 텍스트 및 적요에서 계약자/호실 정보 매칭 (프로젝트 모드 전용) */
const matchContract = (
  text: string,
  contracts: Array<{ value: number; label: string }>
): { value: number; label: string } | null => {
  if (!text || !contracts.length) return null
  const clean = text.replace(/[\s\-_]/g, '')

  // 1. 성명 일치 (2글자 이상)
  for (const c of contracts) {
    const m = c.label.match(/^([가-힣a-zA-Z0-9]+)/)
    if (m && m[1] && m[1].length >= 2) {
      const name = m[1]
      if (clean.includes(name)) return c
    }
  }

  // 2. 동호수 패턴 일치 (예: 101-1001, 101동 1001호, 1001호)
  const unitMatch = clean.match(/(\d{3,4})[동\-]?(\d{3,4})호?/)
  if (unitMatch) {
    const pattern1 = `${unitMatch[1]}-${unitMatch[2]}`
    const pattern2 = `${unitMatch[1]}동${unitMatch[2]}`
    for (const c of contracts) {
      const cClean = c.label.replace(/\s+/g, '')
      if (cClean.includes(pattern1) || cClean.includes(pattern2)) {
        return c
      }
    }
  }

  return null
}

/** 키워드 기반 계정과목 자동 매칭 */
const autoMatchAccount = (
  text: string,
  sort: 1 | 2,
  accounts: Array<{ value: number; label: string; is_cate_only?: boolean }>
): { value: number; label: string } | null => {
  if (!text || !accounts.length) return null
  const lower = text.toLowerCase()
  const availableAccounts = accounts.filter(a => !a.is_cate_only)

  for (const rule of CATEGORY_RULES) {
    if (rule.sort && rule.sort !== sort) continue
    const keywordHit = rule.keywords.some(k => lower.includes(k.toLowerCase()))
    if (!keywordHit) continue

    // 해당 규칙의 대상 계정과목 찾기
    for (const accKw of rule.accountKeywords) {
      const matched = availableAccounts.find(a => a.label.includes(accKw))
      if (matched) return matched
    }
  }

  return null
}

// 주요 국내 은행 식별 힌트
const BANK_NAMES = [
  '국민은행', 'KB국민', '신한은행', '우리은행', '하나은행', '기업은행', 'IBK기업',
  '농협은행', 'NH농협', '농협', '지역농협', '농·축협', '농축협', '축협',
  '수협은행', 'SC제일은행', '씨티은행', '카카오뱅크', '케이뱅크',
  '토스뱅크', '부산은행', '대구은행', '경남은행', '광주은행', '전북은행', '제주은행',
  '우체국', '새마을금고', '신협', '산림조합', '저축은행',
]

export function useBulkTransExcel() {
  const isParsing = ref(false)

  /** 대량 입력 템플릿 다운로드 (예시 행 + 작성안내/참조목록 시트 포함) */
  const downloadBulkTemplate = async (ref_: {
    bankAccounts: Option[]
    accounts: Array<{ label: string; is_cate_only?: boolean }>
    payOrders?: Option[]
    systemType?: BulkSystemType
  }) => {
    const workbook = new ExcelJS.Workbook()
    const ws = workbook.addWorksheet('거래내역 대량입력')
    const relatedLabel = relatedLabelOf(ref_.systemType)
    const isProject = ref_.systemType !== 'company'

    const columns = BULK_COLUMNS.filter(c => isProject || c.key !== 'installment_order_name').map(c => ({
      ...c,
      header: c.header === '__RELATED__' ? relatedLabel : c.header,
    }))
    ws.columns = columns

    const header = ws.getRow(1)
    header.font = { bold: true }
    header.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } }

    const firstBank = ref_.bankAccounts.find(b => b.value)?.label || '(거래계좌명)'
    const accounts = ref_.accounts.filter(a => !a.is_cate_only)
    const accA = accounts[0]?.label || '(계정이름)'
    const accB = accounts[1]?.label || accA

    if (isProject) {
      ws.addRow([1, '2026-01-15', '', firstBank, '예시 적요', '출금', 1500000, accA, '', '', '거래처A', 1000000, '증빙없음'])
      ws.addRow([1, '', '', '', '', '', '', accB, '', '', '거래처B', 500000, '세금계산서'])
      ws.addRow([2, '2026-01-16', '', firstBank, '예시 입금', '입금', 300000, accA, '', '', '거래처C', 300000, ''])
    } else {
      ws.addRow([1, '2026-01-15', '', firstBank, '예시 적요', '출금', 1500000, accA, '', '거래처A', 1000000, '증빙없음'])
      ws.addRow([1, '', '', '', '', '', '', accB, '', '거래처B', 500000, '세금계산서'])
      ws.addRow([2, '2026-01-16', '', firstBank, '예시 입금', '입금', 300000, accA, '', '거래처C', 300000, ''])
    }
    ws.getColumn('deal_date').numFmt = '@'

    const guide = workbook.addWorksheet('작성안내')
    guide.columns = [{ width: 100 }]
    const guideTexts = [
      '■ 작성 방법 및 제한사항',
      `★ [입력 제한] 화면 렌더링 및 안정성을 위해 1회 업로드 시 최대 ${MAX_BULK_ROWS}행 / 은행거래 ${MAX_BULK_TRANSACTIONS}건 이하로 작성해 주세요.`,
      `   - 데이터가 많은 경우 파일을 나누어(예: 30~50건 단위) 순차적으로 등록해 주시기 바랍니다.`,
      '1. 1행 = 회계 계정(분류) 1건입니다. 시트 첫 번째 탭("거래내역 대량입력")에 입력하세요.',
      '2. [그룹번호]는 같은 은행거래에 속하는 행을 묶기 위한 엑셀 내 번호입니다. DB의 거래 번호(pk)가 아니며 저장되지 않습니다.',
      '   - 같은 그룹번호가 연속된 행은 하나의 은행거래로 묶입니다. (1, 2, 3 또는 A, B 등 아무 값이나 가능)',
      '   - 그룹번호를 비워 두면, 거래일자/거래계좌/적요/구분/입출금액 중 하나라도 입력된 행부터 새 은행거래로 인식합니다.',
      '3. 은행거래 정보(거래일자, 메모, 거래계좌, 적요, 구분, 입출금액)는 그룹의 첫 번째 행에만 입력하세요.',
      '4. 같은 그룹의 분류금액 합계는 입출금액과 반드시 일치해야 합니다.',
      '5. 거래일자는 YYYY-MM-DD 형식, 구분은 "입금" 또는 "출금"으로 입력하세요.',
      '6. 거래계좌/계정이름/' + relatedLabel + '은(는) 시스템에 등록된 이름과 정확히 일치해야 합니다. (참조목록 시트 확인)',
    ]
    if (isProject) {
      guideTexts.push(
        '7. 납부회차: 분양대금 또는 분(부)담금 입금 시 지정 (선택사항, 참조목록 시트의 회차명과 일치해야 함. 미지정 시 업로드 팝업 또는 수납 관리에서 사후 지정 가능)',
        '8. 지출증빙: ' + Object.keys(EVIDENCE_TYPE_MAP).join(', '),
        '9. 예시 행(1~3번 거래)은 삭제하고 입력하세요.',
      )
    } else {
      guideTexts.push(
        '7. 지출증빙: ' + Object.keys(EVIDENCE_TYPE_MAP).join(', '),
        '8. 예시 행(1~3번 거래)은 삭제하고 입력하세요.',
      )
    }
    guideTexts.forEach(t => guide.addRow([t]))
    guide.getRow(1).font = { bold: true }
    guide.getRow(2).font = { bold: true, color: { argb: 'FFC00000' } }

    const refSheet = workbook.addWorksheet('참조목록')
    const payOrderNames = isProject && ref_.payOrders ? ref_.payOrders.filter(p => p.value).map(p => p.label) : []

    refSheet.columns = [
      { header: '거래계좌', key: 'bank', width: 30 },
      { header: '계정이름', key: 'acc', width: 30 },
      ...(isProject ? [{ header: '납부회차', key: 'payOrder', width: 25 }] : []),
    ]
    refSheet.getRow(1).font = { bold: true }
    const bankNames = ref_.bankAccounts.filter(b => b.value).map(b => b.label)
    const rows = Math.max(bankNames.length, accounts.length, payOrderNames.length)
    for (let i = 0; i < rows; i++) {
      refSheet.addRow({
        bank: bankNames[i] || '',
        acc: accounts[i]?.label || '',
        ...(isProject ? { payOrder: payOrderNames[i] || '' } : {}),
      })
    }

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `거래내역_대량입력_템플릿_${new Date().getTime()}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
  }

  /**
   * 워크시트 공통 파서: IBS 템플릿 및 인터넷 뱅킹 원본 엑셀 자동 판별 및 변환
   */
  const parseWorksheet = async (ws: ExcelJS.Worksheet, opts: BulkParseOptions): Promise<BulkParseResult> => {
    // 1. 시트 포맷 판별: 1~5행 내에 '그룹번호'나 '분류금액'이 있는지 확인
    let isIbsTemplate = false
    for (let r = 1; r <= Math.min(5, ws.rowCount); r++) {
      const row = ws.getRow(r)
      for (let c = 1; c <= row.cellCount; c++) {
        const val = extractCellValue(row.getCell(c))
        if (val.includes('그룹번호') || val.includes('분류금액')) {
          isIbsTemplate = true
          break
        }
      }
      if (isIbsTemplate) break
    }

    if (isIbsTemplate) {
      return parseIbsTemplateSheet(ws, opts)
    } else {
      return parseBankRawSheet(ws, opts)
    }
  }

  /**
   * 포맷 1: IBS 표준 템플릿 파서 (기존 완벽 호환)
   */
  const parseIbsTemplateSheet = (ws: ExcelJS.Worksheet, opts: BulkParseOptions): BulkParseResult => {
    const transactions: BulkTransaction[] = []
    let current: BulkTransaction | null = null
    let lastKey = ''
    let validRowCount = 0

    const headerRow = ws.getRow(1)
    let colKey = 1, colDate = 2, colNote = 3, colBank = 4, colContent = 5
    let colSort = 6, colBankAmt = 7, colAcc = 8, colContract = 9
    let colPayOrder = -1, colTrader = 10, colEntryAmt = 11, colEvidence = 12

    const headerMap: Record<string, number> = {}
    for (let c = 1; c <= headerRow.cellCount; c++) {
      const text = extractCellValue(headerRow.getCell(c)).trim()
      if (text) headerMap[text] = c
    }

    if (Object.keys(headerMap).length > 0) {
      Object.entries(headerMap).forEach(([text, c]) => {
        if (text.includes('그룹번호')) colKey = c
        else if (text.includes('거래일자')) colDate = c
        else if (text.includes('메모')) colNote = c
        else if (text.includes('거래계좌')) colBank = c
        else if (text.includes('적요')) colContent = c
        else if (text.includes('구분')) colSort = c
        else if (text.includes('입출금액')) colBankAmt = c
        else if (text.includes('계정')) colAcc = c
        else if (text.includes('계약자') || text.includes('관계회사')) colContract = c
        else if (text.includes('납부회차') || text.includes('회차')) colPayOrder = c
        else if (text.includes('거래처')) colTrader = c
        else if (text.includes('분류금액')) colEntryAmt = c
        else if (text.includes('증빙')) colEvidence = c
      })
    }

    for (let i = 2; i <= ws.rowCount; i++) {
      const row = ws.getRow(i)
      const key = extractCellValue(row.getCell(colKey))
      const dealDate = normalizeDate(row.getCell(colDate))
      const note = extractCellValue(row.getCell(colNote))
      const bankName = extractCellValue(row.getCell(colBank))
      const content = extractCellValue(row.getCell(colContent))
      const sortRaw = extractCellValue(row.getCell(colSort))
      const bankAmount = extractCellNumber(row.getCell(colBankAmt))
      const accountName = extractCellValue(row.getCell(colAcc))
      const contractName = extractCellValue(row.getCell(colContract))
      const payOrderName = colPayOrder > 0 ? extractCellValue(row.getCell(colPayOrder)) : ''
      const trader = extractCellValue(row.getCell(colTrader))
      const entryAmount = extractCellNumber(row.getCell(colEntryAmt))
      const rawEvidence = extractCellValue(row.getCell(colEvidence))

      if (
        !key && !dealDate && !bankName && !sortRaw && !content && !note && !bankAmount &&
        !accountName && !trader && !entryAmount && !rawEvidence && !contractName && !payOrderName
      ) {
        continue
      }

      validRowCount++
      if (validRowCount > MAX_BULK_ROWS) {
        throw new Error(
          `1회 업로드 최대 허용 행 수(${MAX_BULK_ROWS}행)를 초과하였습니다.\n파일을 나누어 업로드해 주세요.`,
        )
      }

      const hasBankInfo = !!(dealDate || bankName || sortRaw || content || bankAmount)
      const startsNew = !current || (key ? key !== lastKey : hasBankInfo)

      if (startsNew) {
        if (transactions.length >= MAX_BULK_TRANSACTIONS) {
          throw new Error(
            `1회 업로드 최대 허용 거래 건수(${MAX_BULK_TRANSACTIONS}건)를 초과하였습니다.\n안정적인 처리를 위해 파일을 나누어 등록해 주세요.`,
          )
        }
        const sort = SORT_MAP[sortRaw]
        const bank = opts.bankAccounts.find(b => b.value && b.label === bankName)
        current = {
          key: key || `행${i}`,
          firstRow: i,
          bankForm: {
            deal_date: dealDate,
            bank_account: bank?.value ?? (opts.targetBankAccount ?? ''),
            bank_account_name: bank?.label || '',
            sort: sort ?? 2,
            amount: bankAmount || null,
            content,
            note,
          },
          entries: [],
          entryTotal: 0,
          isBalanced: false,
          errors: [],
          warnings: [],
          isValid: true,
        }
        if (!isValidDate(dealDate)) current.errors.push(`거래일자 '${dealDate}' 형식이 올바르지 않습니다. (YYYY-MM-DD)`)
        if (!bank && !opts.targetBankAccount) current.errors.push(`거래계좌 '${bankName}'을(를) 찾을 수 없습니다.`)
        if (!sort) current.errors.push(`구분 '${sortRaw}'은(는) 입금/출금이어야 합니다.`)
        if (!bankAmount || bankAmount <= 0) current.errors.push('입출금액은 0보다 큰 숫자여야 합니다.')
        if (!content) current.errors.push('적요는 필수 입력 항목입니다.')
        transactions.push(current)
        lastKey = key || current.key
      } else if (current && hasBankInfo) {
        current.warnings.push(`행 ${i}: 같은 그룹번호의 두 번째 이후 행에 입력된 은행거래 정보는 무시됩니다.`)
      }

      const entry: BulkEntry = {
        rowNumber: i,
        account: null,
        account_name: accountName,
        trader,
        amount: entryAmount,
        evidence_type: '',
        contract: null,
        contract_name: contractName,
        installment_order: null,
        installment_order_name: payOrderName,
        errors: [],
        warnings: [],
      }

      const acc = opts.accounts.find(a => !a.is_cate_only && a.label === accountName)
      if (!acc) entry.errors.push(`계정명 '${accountName}'을(를) 찾을 수 없습니다.`)
      else entry.account = acc.value

      if (isNaN(entryAmount) || entryAmount <= 0) entry.errors.push('분류금액은 0보다 큰 숫자여야 합니다.')

      let code = EVIDENCE_TYPE_MAP[rawEvidence]
      if (!code && CODE_TO_EVIDENCE_MAP[rawEvidence]) code = rawEvidence
      if (rawEvidence && !code) entry.errors.push(`지출증빙 '${rawEvidence}'은(는) 유효하지 않습니다.`)
      else entry.evidence_type = (code || '') as BulkEntry['evidence_type']

      if (contractName) {
        const c = opts.contracts.find(o => o.label.includes(contractName))
        if (c) entry.contract = c.value
        else
          entry.warnings.push(
            `${relatedLabelOf(opts.systemType)} '${contractName}'을(를) 찾을 수 없음 - 업로드 후 선택 필요`,
          )
      }

      if (payOrderName && opts.payOrders && opts.payOrders.length) {
        const po = opts.payOrders.find(
          o => o.label === payOrderName || o.label.includes(payOrderName) || payOrderName.includes(o.label),
        )
        if (po && po.value) {
          entry.installment_order = po.value
        } else {
          entry.warnings.push(`납부회차 '${payOrderName}'을(를) 찾을 수 없음 - 업로드 후 선택 필요`)
        }
      }

      current!.entries.push(entry)
    }

    // 그룹별 합계 및 중복 검증 집계
    applyValidationAndDuplicates(transactions, opts.existingTransactions)

    const validTransactions = transactions.filter(t => t.isValid).length
    const duplicateCount = transactions.filter(t => t.isDuplicate).length
    return {
      fileFormat: 'ibs_template',
      transactions,
      summary: {
        transactionCount: transactions.length,
        validTransactions,
        invalidTransactions: transactions.length - validTransactions,
        entryCount: transactions.reduce((s, t) => s + t.entries.length, 0),
        duplicateCount,
      },
      isValid: transactions.length > 0 && validTransactions === transactions.length,
    }
  }

  /**
   * 포맷 2: 인터넷 뱅킹 원본 엑셀 파서 (국민, 신한, 우리, 하나, 기업, 농협 등 자동 감지)
   */
  const parseBankRawSheet = (ws: ExcelJS.Worksheet, opts: BulkParseOptions): BulkParseResult => {
    // 1. 헤더 행 및 은행명 탐색 (1~15행 스캔)
    let headerRowIdx = 1
    let detectedBankName = ''
    let bestScore = 0

    // 은행명 탐색
    for (let r = 1; r <= Math.min(10, ws.rowCount); r++) {
      const row = ws.getRow(r)
      for (let c = 1; c <= row.cellCount; c++) {
        const text = extractCellValue(row.getCell(c))
        for (const bName of BANK_NAMES) {
          if (text.includes(bName)) {
            detectedBankName = bName
            break
          }
        }
        if (detectedBankName) break
      }
      if (detectedBankName) break
    }

    // 헤더 행 탐색 (거래일자, 입금, 출금, 적요, 기재내용 키워드가 가장 많이 포함된 행)
    const keywords = [
      '거래일자', '거래일시', '거래일', '일자', '입금', '출금', '적요', '거래내용',
      '기재내용', '통장인자내용', '잔액', '보낸분', '받는분', '거래처', '의뢰인', '수취인', '송금인',
    ]
    for (let r = 1; r <= Math.min(15, ws.rowCount); r++) {
      const row = ws.getRow(r)
      let score = 0
      for (let c = 1; c <= row.cellCount; c++) {
        const text = extractCellValue(row.getCell(c)).replace(/\s+/g, '')
        if (keywords.some(k => text.includes(k))) score++
      }
      if (score > bestScore) {
        bestScore = score
        headerRowIdx = r
      }
    }

    if (bestScore < 2) {
      throw new Error('인터넷 뱅킹 거래내역 헤더(거래일자, 입출금액, 적요 등)를 찾을 수 없습니다. 엑셀 파일 서식을 확인해 주세요.')
    }

    const headerRow = ws.getRow(headerRowIdx)
    let colDate = -1, colDeposit = -1, colWithdraw = -1, colAmount = -1, colSort = -1
    let colContent = -1, colDesc = -1, colTrader = -1, colNote = -1, colBalance = -1

    for (let c = 1; c <= headerRow.cellCount; c++) {
      const text = extractCellValue(headerRow.getCell(c)).replace(/[\s\-_()]/g, '')
      if (!text) continue

      if (['거래일자', '거래일시', '거래일', '일자', '거래년월일'].some(k => text.includes(k)) && colDate === -1) {
        colDate = c
      } else if (
        !['입금자', '입금인', '입금계좌'].some(k => text.includes(k)) &&
        (['입금액', '맡기신금액', '입금금액', '입금원', '입금된금액'].some(k => text.includes(k)) ||
          text === '입금' ||
          /^입금[금액원()]*$/.test(text)) &&
        colDeposit === -1
      ) {
        colDeposit = c
      } else if (
        !['출금계좌'].some(k => text.includes(k)) &&
        (['출금액', '찾으신금액', '출금금액', '출금원', '지급금액', '지급액'].some(k => text.includes(k)) ||
          text === '출금' ||
          /^출금[금액원()]*$/.test(text)) &&
        colWithdraw === -1
      ) {
        colWithdraw = c
      } else if (['거래금액', '금액'].some(k => text.includes(k)) && colAmount === -1) {
        colAmount = c
      } else if (['거래구분', '구분', '입출구분', '거래종류'].some(k => text.includes(k)) && colSort === -1) {
        colSort = c
      } else if (['기재내용', '통장인자내용', '통장메모'].some(k => text.includes(k)) && colDesc === -1) {
        colDesc = c
      } else if (['적요', '적요명', '거래내용', '통장적요', '내용'].some(k => text.includes(k)) && colContent === -1) {
        colContent = c
      } else if (
        [
          '보낸분/받는분', '보낸분받는분', '거래처', '입금자', '수취인',
          '상대예금주', '상대계좌예금주', '상대계좌예금주명', '상대방',
          '의뢰인', '송금의뢰인', '송금인', '입금인', '송금인/수취인', '의뢰인/수취인',
        ].some(k => text.includes(k)) &&
        colTrader === -1
      ) {
        colTrader = c
      } else if (['취급점', '거래점', '영업점', '메모', '비고'].some(k => text.includes(k)) && colNote === -1) {
        colNote = c
      } else if (['잔액', '거래후잔액', '현재잔액'].some(k => text.includes(k)) && colBalance === -1) {
        colBalance = c
      }
    }

    if (colDate === -1 || (colDeposit === -1 && colWithdraw === -1 && colAmount === -1)) {
      throw new Error('거래일자 또는 입출금 금액 열을 식별할 수 없습니다. 서식을 확인해 주세요.')
    }

    // 기본 대상 계좌 결정: opts.targetBankAccount -> 단일 계좌 자동 선택 -> 없음
    let defaultBank = opts.bankAccounts.find(b => b.value === opts.targetBankAccount)
    if (!defaultBank) {
      const nonNullBanks = opts.bankAccounts.filter(b => b.value)
      if (nonNullBanks.length === 1) defaultBank = nonNullBanks[0]
    }

    const transactions: BulkTransaction[] = []
    let validRowCount = 0

    for (let r = headerRowIdx + 1; r <= ws.rowCount; r++) {
      const row = ws.getRow(r)
      const dealDateRaw = colDate > 0 ? row.getCell(colDate) : ''
      const dealDate = normalizeDate(dealDateRaw)

      // 날짜가 없거나 유효하지 않으면 요약행(합계, 소계, 안내문 등)으로 간주하고 건너뜀
      if (!isValidDate(dealDate)) continue

      let deposit = colDeposit > 0 ? extractCellNumber(row.getCell(colDeposit)) : 0
      let withdraw = colWithdraw > 0 ? extractCellNumber(row.getCell(colWithdraw)) : 0
      let singleAmt = colAmount > 0 ? extractCellNumber(row.getCell(colAmount)) : 0
      let sortText = colSort > 0 ? extractCellValue(row.getCell(colSort)) : ''

      let sort: 1 | 2 = 2
      let amount = 0

      if (colDeposit > 0 || colWithdraw > 0) {
        if (deposit > 0) {
          sort = 1
          amount = deposit
        } else if (withdraw > 0) {
          sort = 2
          amount = withdraw
        } else {
          continue // 금액이 0이거나 없는 행 건너뜀
        }
      } else if (singleAmt > 0) {
        amount = singleAmt
        sort = sortText.includes('입금') ? 1 : 2
      } else {
        continue
      }

      validRowCount++
      if (validRowCount > MAX_BULK_ROWS) {
        throw new Error(
          `1회 업로드 최대 허용 행 수(${MAX_BULK_ROWS}건)를 초과하였습니다.\n파일을 기간별로 나누어 업로드해 주세요.`,
        )
      }

      let content = colContent > 0 ? extractCellValue(row.getCell(colContent)) : ''
      const desc = colDesc > 0 ? extractCellValue(row.getCell(colDesc)) : ''
      let trader = colTrader > 0 ? extractCellValue(row.getCell(colTrader)) : ''
      const note = colNote > 0 ? extractCellValue(row.getCell(colNote)) : ''

      // 농협 등에서 적요는 "전자금융"이고 기재내용에 실제 메모(홍길동, 공사비 등)가 있는 경우 병합/대체
      if (desc) {
        if (!content) {
          content = desc
        } else if (['대체', '전자금융', '타행', '타행이체', '현금', 'CD', 'ATM'].includes(content.trim())) {
          content = desc
        } else if (!content.includes(desc)) {
          content = `${content} ${desc}`
        }
      }

      if (!content && trader) content = trader
      if (!trader && desc) trader = desc
      if (!trader && content) trader = content
      if (!content) content = sort === 1 ? '통장입금' : '통장출금'

      // 계정과목 및 계약자 자동 추천 (규칙 기반)
      const textToMatch = `${content} ${trader} ${note}`
      const matchedAcc = autoMatchAccount(textToMatch, sort, opts.accounts)
      const matchedContract = opts.systemType === 'project' && sort === 1 ? matchContract(textToMatch, opts.contracts) : null

      const txErrors: string[] = []
      const txWarnings: string[] = []

      if (!defaultBank) {
        txErrors.push('거래계좌가 지정되지 않았습니다. (상단 일괄 지정 필요)')
      }

      // 분개 항목 구성
      const entryErrors: string[] = []
      const entryWarnings: string[] = []

      let accountId: number | null = matchedAcc?.value ?? null
      let accountName = matchedAcc?.label ?? ''

      // 프로젝트 모드이고 입금인데 계정이 없는 경우 '분양수입금'/'분담금' 기본 추천 시도
      if (!accountId && opts.systemType === 'project' && sort === 1) {
        const salesAcc = opts.accounts.find(a => !a.is_cate_only && (a.label.includes('분양수입') || a.label.includes('분담금')))
        if (salesAcc) {
          accountId = salesAcc.value
          accountName = salesAcc.label
        }
      }

      if (!accountId) {
        entryErrors.push('계정과목을 지정해 주세요. (상단 일괄 지정 필요)')
      }

      const entry: BulkEntry = {
        rowNumber: r,
        account: accountId,
        account_name: accountName,
        trader,
        amount,
        evidence_type: '',
        contract: matchedContract?.value ?? null,
        contract_name: matchedContract?.label ?? '',
        installment_order: null,
        installment_order_name: '',
        isAutoMatched: !!matchedAcc,
        isContractAutoMatched: !!matchedContract,
        errors: entryErrors,
        warnings: entryWarnings,
      }

      const tx: BulkTransaction = {
        key: String(transactions.length + 1),
        firstRow: r,
        bankForm: {
          deal_date: dealDate,
          bank_account: defaultBank?.value ?? '',
          bank_account_name: defaultBank?.label || '',
          sort,
          amount,
          content,
          note,
        },
        entries: [entry],
        entryTotal: amount,
        isBalanced: true,
        errors: txErrors,
        warnings: txWarnings,
        isValid: txErrors.length === 0 && entryErrors.length === 0,
      }

      transactions.push(tx)
    }

    // 중복 검증 집계
    applyValidationAndDuplicates(transactions, opts.existingTransactions)

    const validTransactions = transactions.filter(t => t.isValid).length
    const duplicateCount = transactions.filter(t => t.isDuplicate).length

    return {
      fileFormat: 'bank_raw',
      detectedBankName,
      transactions,
      summary: {
        transactionCount: transactions.length,
        validTransactions,
        invalidTransactions: transactions.length - validTransactions,
        entryCount: transactions.reduce((s, t) => s + t.entries.length, 0),
        duplicateCount,
      },
      isValid: transactions.length > 0 && validTransactions === transactions.length,
    }
  }

  /**
   * 중복 거래 검증 및 오류/유효성 집계 헬퍼
   */
  const applyValidationAndDuplicates = (
    transactions: BulkTransaction[],
    existing?: ExistingTransactionRef[]
  ) => {
    for (const t of transactions) {
      t.entryTotal = t.entries.reduce((s, e) => s + (e.amount > 0 ? e.amount : 0), 0)
      t.isBalanced = !!t.bankForm.amount && Math.abs(t.entryTotal - t.bankForm.amount) < 0.01

      if (!t.isBalanced) {
        t.errors.push(
          `거래 금액(${(t.bankForm.amount ?? 0).toLocaleString()})과 분류 금액 합계(${t.entryTotal.toLocaleString()})가 일치하지 않습니다.`,
        )
      }

      // 기등록 거래와 중복 여부 확인
      if (existing && existing.length > 0) {
        const isDup = existing.some(
          ex =>
            ex.deal_date === t.bankForm.deal_date &&
            ex.amount === t.bankForm.amount &&
            ex.sort === t.bankForm.sort &&
            (ex.content === t.bankForm.content || (t.entries[0] && ex.content === t.entries[0].trader))
        )
        if (isDup) {
          t.isDuplicate = true
          t.duplicateReason = '기등록 거래와 일치 (일자, 구분, 금액, 적요)'
          t.warnings.push('⚠ 동일 일자·금액의 기존 거래가 이미 등록되어 있습니다.')
        }
      }

      t.isValid = t.errors.length === 0 && t.entries.every(e => e.errors.length === 0)
    }
  }

  /** 구분자(TSV/CSV) 라인 분리 헬퍼 */
  const parseDelimitedLine = (line: string, delimiter: string): string[] => {
    if (delimiter === '\t') return line.split('\t')
    const result: string[] = []
    let cur = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          cur += '"'
          i++
        } else {
          inQuotes = !inQuotes
        }
      } else if (char === delimiter && !inQuotes) {
        result.push(cur.trim())
        cur = ''
      } else {
        cur += char
      }
    }
    result.push(cur.trim())
    return result
  }

  /** 엑셀/CSV 파일 파싱 (IBS 표준 템플릿 및 은행 원본 서식 자동 지원) */
  const parseBulkFile = async (file: File, opts: BulkParseOptions): Promise<BulkParseResult> => {
    isParsing.value = true
    try {
      if (file.name.toLowerCase().endsWith('.csv')) {
        const text = await file.text()
        return await parseBulkText(text, opts)
      }
      const workbook = new ExcelJS.Workbook()
      await workbook.xlsx.load(await file.arrayBuffer())
      const ws = workbook.worksheets[0]
      if (!ws) throw new Error('엑셀 파일에 워크시트가 없습니다.')
      return await parseWorksheet(ws, opts)
    } finally {
      isParsing.value = false
    }
  }

  /** 클립보드 텍스트(TSV) 및 CSV 파싱 */
  const parseBulkText = async (text: string, opts: BulkParseOptions): Promise<BulkParseResult> => {
    isParsing.value = true
    try {
      const workbook = new ExcelJS.Workbook()
      const ws = workbook.addWorksheet('ClipboardData')
      const lines = text.trim().split(/\r?\n/)
      const delimiter = text.includes('\t') ? '\t' : ','
      for (const line of lines) {
        if (!line.trim()) continue
        ws.addRow(parseDelimitedLine(line, delimiter))
      }
      return await parseWorksheet(ws, opts)
    } finally {
      isParsing.value = false
    }
  }

  return { isParsing, downloadBulkTemplate, parseBulkFile, parseBulkText }
}
