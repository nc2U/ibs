import { numFormat } from '@/utils/baseMixins'

/** 증감액을 부호(+)와 함께 표시. 0이면 '-' */
export const formatSigned = (val: number) => {
  if (!val) return '-'
  const prefix = val > 0 ? '+' : ''
  return `${prefix}${numFormat(val)}`
}

/** 증감 색상 클래스. 지출은 감소가 긍정이므로 invertColor=true */
export const diffClass = (val: number, invertColor = false) => {
  if (!val) return 'text-muted'
  const isPositive = invertColor ? val < 0 : val > 0
  return isPositive ? 'text-primary fw-semibold' : 'text-danger fw-semibold'
}

/** 구성비(%) 문자열 */
export const calcShare = (amount: number, total: number) => {
  if (!total || !amount) return '-'
  return `${((amount / total) * 100).toFixed(1)}%`
}
