import { ref } from 'vue'
import ExcelJS from 'exceljs'
import type { AccountPicker } from '@/store/types/comLedger'

export interface ParsedEntry {
  // Excel data
  account_name: string
  account?: number // resolved from picker options
  trader: string
  amount: number
  evidence_type: string // This will hold the code '0', '1', etc.
  raw_evidence_type: string // This will hold the original Korean name from Excel
  contract_or_affiliate_name?: string
  contract?: number // for 프로젝트 (resolved if name matches)
  affiliate?: number // for 본사 (resolved if name matches)

  // Matching info
  existingPk?: number // pk from an existing entry (for updates)
  rowNumber: number
  operationType: 'update' | 'create' // update = has pk, create = no pk

  // Validation
  isValid: boolean
  validationErrors: string[]
  validationWarnings: string[] // non-blocking warnings (e.g., contract name not found)
}

export interface ExistingEntry {
  pk?: number
  account?: number
  account_name?: string
  trader?: string
  amount?: number
  evidence_type?: string
  contract?: number
  contract_name?: string
  affiliate?: number
  affiliate_name?: string
}

export interface ParseResult {
  entriesToUpdate: ParsedEntry[] // has existingPk
  entriesToCreate: ParsedEntry[] // no existingPk
  entriesToDelete: ExistingEntry[] // existing entries beyond Excel row count
  totalAmount: number
  isValid: boolean
  validationSummary: {
    totalRows: number
    validRows: number
    invalidRows: number
    updateCount: number
    createCount: number
    deleteCount: number
  }
}

const EVIDENCE_TYPE_MAP: { [key: string]: string } = {
  증빙없음: '0',
  세금계산서: '1',
  '계산서(면세)': '2',
  '신용/체크카드 매출전표': '3',
  현금영수증: '4',
  '원천징수영수증/지급명세서': '5',
  '지로용지 및 청구서': '6',
}

export function useExcelUpload() {
  const isUploading = ref(false)
  const uploadError = ref<string | null>(null)

  const parseExcelFile = async (
    file: File,
    accountOptions: AccountPicker[],
    existingEntries: ExistingEntry[],
    transactionAmount: number,
    systemType: 'company' | 'project',
    contractOrAffiliateOptions?: Array<{ value: number; label: string }>, // for name matching
  ): Promise<ParseResult> => {
    isUploading.value = true
    uploadError.value = null

    try {
      const workbook = new ExcelJS.Workbook()
      const buffer = await file.arrayBuffer()
      await workbook.xlsx.load(buffer)

      const worksheet = workbook.worksheets[0]
      if (!worksheet) {
        throw new Error('엑셀 파일에 워크시트가 없습니다.')
      }

      const parsedEntries: ParsedEntry[] = []
      let totalAmount = 0
      let excelRowIndex = 0

      // Skip the header row, start from row 2
      for (let i = 2; i <= worksheet.rowCount; i++) {
        const row = worksheet.getRow(i)

        // Skip empty rows
        if (!row.getCell(1).value && !row.getCell(4).value) continue

        const rawEvidenceType = String(row.getCell(4).value || '').trim()
        const contractOrAffiliateName = String(row.getCell(5).value || '').trim()

        const entry: ParsedEntry = {
          account_name: String(row.getCell(1).value || '').trim(),
          // description: String(row.getCell(2).value || '').trim(),
          trader: String(row.getCell(2).value || '').trim(),
          amount: parseFloat(String(row.getCell(3).value || '0')),
          evidence_type: '', // Will be replaced by code
          raw_evidence_type: rawEvidenceType, // Keep original string for display
          contract_or_affiliate_name: contractOrAffiliateName,
          rowNumber: i,
          isValid: true,
          validationErrors: [],
          validationWarnings: [],
          operationType: 'create', // default, will be changed if matched with existing
        }

        // Validate and convert evidence_type
        const mappedEvidenceType = EVIDENCE_TYPE_MAP[rawEvidenceType]
        if (rawEvidenceType && !mappedEvidenceType) {
          entry.isValid = false
          entry.validationErrors.push(`지출증빙 '${rawEvidenceType}'은 유효하지 않습니다.`)
        } else {
          entry.evidence_type = mappedEvidenceType || '' // 매핑된 값 또는 빈 문자열 (rawEvidenceType이 빈 경우)
        }

        // Match with existing entry by order (if exists)
        if (excelRowIndex < existingEntries.length) {
          const existingEntry = existingEntries[excelRowIndex]
          if (existingEntry.pk) {
            entry.existingPk = existingEntry.pk
            entry.operationType = 'update'
          }
        }

        // Validate account name
        const matchingAccount = accountOptions.find(
          opt => !opt.is_cate_only && opt.label === entry.account_name,
        )
        if (!matchingAccount) {
          entry.isValid = false
          entry.validationErrors.push(`계정명 '${entry.account_name}'을 찾을 수 없습니다.`)
        } else {
          entry.account = matchingAccount.value
        }

        // Validate amount
        if (isNaN(entry.amount) || entry.amount <= 0) {
          entry.isValid = false
          entry.validationErrors.push('금액은 0보다 큰 숫자여야 합니다.')
        } else {
          totalAmount += entry.amount
        }

        // Try to match contract/affiliate name if provided
        if (contractOrAffiliateName && contractOrAffiliateOptions) {
          const matchingContractOrAffiliate = contractOrAffiliateOptions.find(
            opt => opt.label.split('(')[0] === contractOrAffiliateName,
          )
          if (matchingContractOrAffiliate) {
            if (systemType === 'project') {
              entry.contract = matchingContractOrAffiliate.value
            } else {
              entry.affiliate = matchingContractOrAffiliate.value
            }
          } else {
            // Not found - add warning but don't invalidate
            entry.validationWarnings.push(
              `⚠️ ${systemType === 'project' ? '계약자' : '관계회사(프로젝트)'} '${contractOrAffiliateName}'를 찾을 수 없음 - 업로드 후 선택 필요`,
            )
          }
        }

        parsedEntries.push(entry)
        excelRowIndex++
      }

      // Identify entries to delete (existing entries beyond Excel row count)
      const entriesToDelete: ExistingEntry[] = []
      if (excelRowIndex < existingEntries.length) {
        for (let i = excelRowIndex; i < existingEntries.length; i++) {
          entriesToDelete.push(existingEntries[i])
        }
      }

      // Categorize parsed entries
      const entriesToUpdate = parsedEntries.filter(e => e.operationType === 'update')
      const entriesToCreate = parsedEntries.filter(e => e.operationType === 'create')

      // Validate total amount matches transaction amount (must be exact, 0 difference)
      const amountDiff = Math.abs(totalAmount - transactionAmount)
      const isAmountValid = amountDiff === 0

      return {
        entriesToUpdate,
        entriesToCreate,
        entriesToDelete,
        totalAmount,
        isValid: isAmountValid && parsedEntries.every(e => e.isValid),
        validationSummary: {
          totalRows: parsedEntries.length,
          validRows: parsedEntries.filter(e => e.isValid).length,
          invalidRows: parsedEntries.filter(e => !e.isValid).length,
          updateCount: entriesToUpdate.length,
          createCount: entriesToCreate.length,
          deleteCount: entriesToDelete.length,
        },
      }
    } catch (error) {
      uploadError.value =
        error instanceof Error ? error.message : '파일 파싱 중 오류가 발생했습니다.'
      throw error
    } finally {
      isUploading.value = false
    }
  }

  const downloadTemplate = async (
    transactionData: {
      amount: number
      entries: Array<{
        account_name?: string
        trader?: string
        amount?: number
        evidence_type?: string
        contract_name?: string
        affiliate_name?: string
      }>
    },
    systemType: 'company' | 'project',
  ) => {
    const workbook = new ExcelJS.Workbook()
    const worksheet = workbook.addWorksheet('회계 계정 정보')

    // Set column widths
    worksheet.columns = [
      { header: '계정이름', key: 'account_name', width: 25 },
      { header: '거래처', key: 'trader', width: 30 },
      { header: '금액', key: 'amount', width: 25 },
      { header: '지출증빙', key: 'evidence_type', width: 20 },
      {
        header: systemType === 'project' ? '계약자' : '관계회사(프로젝트)',
        key: 'contract_or_affiliate',
        width: 25,
      },
    ]

    // Style header row
    const headerRow = worksheet.getRow(1)
    headerRow.font = { bold: true }
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE0E0E0' },
    }

    // Add existing entries or empty template row
    if (transactionData.entries.length > 0) {
      transactionData.entries.forEach(entry => {
        worksheet.addRow({
          account_name: entry.account_name || '',
          trader: entry.trader || '',
          amount: entry.amount || '',
          evidence_type: entry.evidence_type || '',
          contract_or_affiliate:
            systemType === 'project' ? entry.contract_name || '' : entry.affiliate_name || '',
        })
      })
    } else {
      // Add single empty row for template
      worksheet.addRow({
        account_name: '',
        trader: '',
        amount: '',
        evidence_type: '',
        contract_or_affiliate: '',
      })
    }

    // Generate and download
    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `회계계정정보_템플릿_${new Date().getTime()}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
  }

  return {
    isUploading,
    uploadError,
    parseExcelFile,
    downloadTemplate,
  }
}
