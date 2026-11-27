import { getToday } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { PermissionCode } from '@/store/constants/permissions'
import type { User } from '@/store/types/accounts'
import type { Company, CompanySeal } from '@/store/types/settings'
import type { OfficialLetter, OfficialLetterSealDetail } from '@/store/types/docs'

export interface RepresentativeInfo {
  title: string
  name: string
}

export interface SenderContact {
  phone: string
  fax: string
  email: string
}

const DELEGATION_DUTY_TITLES = new Set([
  '현장소장',
  '프로젝트 PM',
  '프로젝트PM',
  'PM',
  '소장',
  '본부장',
  '팀장',
])

/** KST 로컬 기준 YYYY-MM-DD 오늘 날짜 반환 */
export const getLocalTodayStr = (): string => getToday()

/** 전결 처리가 가능한 중간 직책 여부 판별 */
export const isDelegationDutyTitle = (title?: string | null): boolean =>
  !!title && DELEGATION_DUTY_TITLES.has(title)

/** 기안/승인자 성명에서 중복 표기를 막기 위해 직함 토큰 제거 */
export const stripDrafterTitles = (name?: string | null): string => {
  return (name || '').replace(/현장소장|대표이사|본부장|대표|사장|소장|팀장/g, '').trim()
}

/** 회사 대표이사 목록 및 단독/공동대표 직함 파싱 */
export const parseRepresentatives = (
  ceo?: string | null,
  forceJoint = false,
): RepresentativeInfo[] => {
  if (!ceo) return []
  const parts = ceo
    .replace(/;/g, ',')
    .split(',')
    .map(p => p.trim())
    .filter(Boolean)
  const isJoint = parts.length > 1 || forceJoint
  return parts.map(name => ({
    title: isJoint ? '공동대표이사' : '대표이사',
    name,
  }))
}

/** 기본 대표이사 성명 추출 */
export const resolveRepresentativeName = (
  company?: Company | null,
  reps?: RepresentativeInfo[],
): string => {
  const list = reps ?? parseRepresentatives(company?.ceo)
  return (
    list[0]?.name || company?.representative_name || company?.ceo?.split(',')?.[0]?.trim() || ''
  )
}

/** 최종 승인(전결)권자 직책 산출 */
export const resolveApproverDutyTitle = (
  senderDutyTitle?: string | null,
  seal?: CompanySeal | OfficialLetterSealDetail | null,
): string => {
  if (senderDutyTitle) return senderDutyTitle
  if (seal?.internal_manager_duty) return seal.internal_manager_duty
  return seal?.final_approval_duty_name || '대표이사'
}

/** 최종 승인(전결)권자 성명 산출 */
export const resolveFinalApproverName = (params: {
  senderName?: string | null
  seal?: CompanySeal | OfficialLetterSealDetail | null
  dutyTitle: string
  cleanDrafter: string
  representativeName: string
}): string => {
  const { senderName, seal, dutyTitle, cleanDrafter, representativeName } = params
  if (senderName) return senderName
  if (seal?.internal_manager_name) return seal.internal_manager_name
  if (isDelegationDutyTitle(dutyTitle)) {
    return cleanDrafter || representativeName || '전결권자'
  }
  return representativeName || cleanDrafter || '대표이사'
}

/** 공문서 하단 발신 연락처 산출 (서버 계산값 또는 기안자 직통 연락처 우선, 회사 대표번호 폴백) */
export const resolveSenderContact = (params: {
  company?: Company | null
  letter?: OfficialLetter | null
  userInfo?: User | null
  approvalMode?: 'approval' | 'manual'
}): SenderContact => {
  const { company, letter, userInfo, approvalMode = 'manual' } = params
  const serverContact = letter?.sender_contact
  if (serverContact) {
    return {
      phone: serverContact.phone || company?.phone || '-',
      fax: serverContact.fax || company?.fax || '-',
      email: serverContact.email || company?.email || '',
    }
  }
  const useStaffDirect = approvalMode === 'approval'
  return {
    phone: (useStaffDirect ? userInfo?.staff_phone : '') || company?.phone || '-',
    fax: (useStaffDirect ? userInfo?.staff_fax : '') || company?.fax || '-',
    email: (useStaffDirect ? userInfo?.email : '') || company?.email || '',
  }
}

/** 기본주소 · 상세주소 · 참고항목을 표준 도로명 표기로 조합 */
export const composeAddress = (addr1: string, detail: string, addr3: string): string => {
  const parts: string[] = []
  if (addr1.trim()) parts.push(addr1.trim())
  if (detail.trim()) parts.push(detail.trim())
  if (addr3.trim()) {
    const cleanRef = addr3.trim()
    parts.push(cleanRef.startsWith('(') ? cleanRef : `(${cleanRef})`)
  }
  return parts.join(' ')
}

/** 저장된 단일 주소 문자열에서 후행 참고항목 `(동/건물명)`을 분리 */
export const splitStoredAddress = (
  address?: string | null,
): { base: string; detail: string; ref: string } => {
  const raw = (address || '').trim()
  if (!raw) return { base: '', detail: '', ref: '' }
  const match = raw.match(/^(.*?)\s+(\([^()]+\))$/)
  if (match && match[1].trim()) {
    return { base: match[1].trim(), detail: '', ref: match[2].trim() }
  }
  return { base: raw, detail: '', ref: '' }
}

/** YYYY-MM-DD 단축 날짜 포맷 */
export const formatShortDate = (dateStr?: string | null): string => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

/** YYYY-MM-DD HH:MM(:SS) 날짜/시간 포맷 */
export const formatDateTimeStr = (dateStr?: string | null, withSeconds = false): string => {
  if (!dateStr) return '-'
  const endIdx = withSeconds ? 19 : 16
  return dateStr.substring(0, endIdx).replace('T', ' ')
}

/** URL 쿼리·해시를 제거한 소문자 확장자 추출 */
export const getFileExt = (fileUrl?: string | null): string => {
  if (!fileUrl) return ''
  const cleanUrl = fileUrl.split('?')[0].split('#')[0]
  const parts = cleanUrl.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
}

/** URL에서 디코딩된 파일명 추출 */
export const getFileNameFromUrl = (fileUrl?: string | null): string => {
  if (!fileUrl) return ''
  const cleanUrl = fileUrl.split('?')[0].split('#')[0]
  const rawName = cleanUrl.split('/').pop() || ''
  try {
    return decodeURIComponent(rawName)
  } catch {
    return rawName
  }
}

/** 확장자 기준 스캔 원본 아이콘 반환 */
export const getScanFileIcon = (fileUrl?: string | null): string => {
  const ext = getFileExt(fileUrl)
  if (!ext) return 'mdi-file-document-outline'
  if (ext === 'pdf') return 'mdi-file-pdf-box'
  if (ext === 'hwp' || ext === 'hwpx') return 'mdi-file-document-outline'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'tif', 'tiff'].includes(ext)) {
    return 'mdi-file-image'
  }
  return 'mdi-file-document'
}

/** 수신 공문 회신기한 D-Day 뱃지 색상 */
export const getDDayBadgeColor = (dDay?: number | null): string => {
  if (dDay === null || dDay === undefined) return 'secondary'
  if (dDay < 0) return 'danger'
  if (dDay === 0) return 'warning'
  if (dDay <= 3) return 'danger'
  if (dDay <= 7) return 'warning'
  return 'info'
}

/** 수신 공문 회신기한 D-Day 라벨 텍스트 */
export const getDDayText = (dDay?: number | null, detailed = false): string => {
  if (dDay === null || dDay === undefined) return ''
  if (dDay < 0) {
    return detailed ? `기한초과 (D+${Math.abs(dDay)})` : `D+${Math.abs(dDay)}`
  }
  if (dDay === 0) return detailed ? '오늘 마감 (D-Day)' : 'D-Day'
  return detailed ? `${dDay}일 남음 (D-${dDay})` : `D-${dDay}`
}

/** 현재 선택된 회사의 본사(type='1') 워크스페이스 기준 문서 권한 판정 */
export const useLetterPerms = () => {
  const { can, canGlobal, PERM } = usePerms()
  const accStore = useAccount()
  const comStore = useCompany()

  const hasPerm = (code: PermissionCode): boolean => {
    const isStaffOrSuper = Boolean(accStore.superAuth || accStore.isStaff)
    if (!isStaffOrSuper) return false
    const hqProjId = comStore.company?.com_issue_project
    return hqProjId ? can(code, hqProjId) : canGlobal(code)
  }

  return { accStore, comStore, hasPerm, PERM }
}
