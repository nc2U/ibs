export const numFormat = (val: number | string, n = 0, zero: string | 0 = '-') => {
  const parsed = Number(val)
  const value = Number.isFinite(parsed) ? parsed : 0
  const parts = value.toFixed(n).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return !value ? zero : parts.join('.')
}

export const cutString = (str: string | null | undefined = '', len = 20, abb = '...') => {
  if (!str) return ''
  return str.length > len ? `${str.substring(0, len)}${abb}` : str
}

export const diffDate = (date1: Date | string, date2?: Date | string) => {
  const start = typeof date1 === 'string' ? new Date(date1) : date1
  const now = !date2 ? new Date() : typeof date2 === 'string' ? new Date(date2) : date2
  const between = now.getTime() - start.getTime()
  return between / 1000 / 60 / 60 / 24
}

export const addDays = (date: Date, days: number) => date.setDate(date.getDate() + days)

export const addDaysToDate = (dateString: Date | string, days: number) => {
  let date: Date
  if (typeof dateString === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [y, m, d] = dateString.split('-').map(Number)
    date = new Date(y, m - 1, d)
  } else {
    date = new Date(dateString)
  }
  date.setDate(date.getDate() + days)

  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')

  return `${year}-${month}-${day}`
}

export const dateFormat = (date: Date | string, split: string = '-') => {
  const d = date instanceof Date ? new Date(date.getTime()) : new Date(date)
  if (Number.isNaN(d.getTime())) return ''
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return [yyyy, mm, dd].join(split)
}

export const getToday = () =>
  new Date(new Date().getTime() + 32400000).toISOString().replace(/T.*$/, '')

export const timeFormat = (
  date: Date | string | number,
  dp: 'short' | 'min' | 'full' = 'full',
  split: string = '-',
) => {
  const d = date instanceof Date ? new Date(date.getTime()) : new Date(date)
  if (Number.isNaN(d.getTime())) return ''
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')

  if (dp === 'short') return `${hh}:${min}`
  if (dp === 'min') return `${yyyy}${split}${mm}${split}${dd} ${hh}:${min}`
  return `${yyyy}${split}${mm}${split}${dd} ${hh}:${min}:${ss}`
}

export const elapsedTime = (input?: Date | number | string): string => {
  if (!input) return ''
  const start = new Date(input)
  if (Number.isNaN(start.getTime())) return ''
  const now = new Date()

  const diff = Math.floor((now.getTime() - start.getTime()) / 1000)
  if (diff < 0) return '방금 전'

  const units = [
    { name: '년', seconds: 60 * 60 * 24 * 365 },
    { name: '달', seconds: 60 * 60 * 24 * 30 },
    { name: '주', seconds: 60 * 60 * 24 * 7 },
    { name: '일', seconds: 60 * 60 * 24 },
    { name: '시간', seconds: 60 * 60 },
    { name: '분', seconds: 60 },
  ]

  for (const unit of units) {
    const elapsed = Math.floor(diff / unit.seconds)
    if (elapsed >= 1) return `${elapsed}${unit.name} 전`
  }

  return '방금 전'
}

export const numberToHour = (digit: number | string) => {
  const a = Math.floor(Number(digit))
  const b = Math.round((Number(digit) - a) * 60)
  const c = b < 10 ? '0' : ''
  return String(a) + ':' + c + String(b)
}

export const humanizeFileSize = (bytes?: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'
  if (bytes === undefined || bytes === null || !Number.isFinite(bytes) || bytes < 0) return ''

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1)

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const escapeHtml = (str: string): string =>
  str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

export const toPrint = (title: string) => {
  const printContent = document.getElementById('print-area')?.cloneNode(true)
  const html = printContent instanceof Element ? printContent.innerHTML : ''

  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.opener = null
    printWindow.document.open()
    printWindow.document.write(`<html><head><title>${escapeHtml(title)}</title></head><body>`)
    printWindow.document.write(html)
    printWindow.document.write('</body></html>')
    printWindow.document.close()

    printWindow.print()
    printWindow.close()
  }
}

export const getMeetingStatusColor = (status: string): string => {
  if (status === '1') return 'info'
  if (status === '2') return 'success'
  return 'secondary'
}

export const parseRrnMeta = (rawRrn: string): { birthDate: string; gender: 'M' | 'F' } | null => {
  const digits = String(rawRrn || '').replace(/\D/g, '')
  if (digits.length !== 13) return null

  const yy = Number(digits.slice(0, 2))
  const mm = Number(digits.slice(2, 4))
  const dd = Number(digits.slice(4, 6))
  const genderCode = digits[6]

  const centuryMap: Record<string, number> = {
    '1': 1900,
    '2': 1900,
    '5': 1900,
    '6': 1900,
    '3': 2000,
    '4': 2000,
    '7': 2000,
    '8': 2000,
    '9': 1800,
    '0': 1800,
  }
  const century = centuryMap[genderCode]
  if (century === undefined) return null

  const fullYear = century + yy
  const dt = new Date(fullYear, mm - 1, dd)
  if (
    Number.isNaN(dt.getTime()) ||
    dt.getFullYear() !== fullYear ||
    dt.getMonth() !== mm - 1 ||
    dt.getDate() !== dd
  ) {
    return null
  }

  const gender: 'M' | 'F' = ['1', '3', '5', '7', '9'].includes(genderCode) ? 'M' : 'F'
  const birthDate = `${fullYear}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`
  return { birthDate, gender }
}
