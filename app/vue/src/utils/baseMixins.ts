export const numFormat = (val: number | string, n = 0, zero: string | 0 = '-') => {
  const value = Number.isNaN(val) ? 0 : Number(val)
  const parts = value.toFixed(n).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return !value || value === 0 ? zero : parts.join('.')
}

export const cutString = (str: string | null | undefined = '', len = 20, abb = '...') => {
  if (!str) return ''
  return str.length > len ? `${str.substring(0, len)}${abb}` : str
}

export const diffDate = (date1: Date | string, date2?: Date) => {
  const start = typeof date1 === 'string' ? new Date(date1) : date1
  const now = !date2 ? new Date() : date2
  const between = now.getTime() - start.getTime()
  return between / 1000 / 60 / 60 / 24
}

export const addDays = (date: Date, days: number) => date.setDate(date.getDate() + days)

export const addDaysToDate = (dateString: Date | string, days: number) => {
  const date = new Date(dateString)
  date.setDate(date.getDate() + days)

  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')

  return `${year}-${month}-${day}`
}

export const dateFormat = (date: Date | string, split: string = '-') => {
  const d = new Date(date instanceof Date ? date : new Date(date))
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return [yyyy, mm, dd].join(split)
}

export const getToday = () =>
  new Date(new Date().getTime() + 32400000).toISOString().replace(/T.*$/, '')

export const timeFormat = (date: Date | string | number, short = false, split: string = '-') => {
  const d = new Date(date instanceof Date ? date : new Date(date))
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')

  if (short) return `${hh}:${min}`
  return `${yyyy}${split}${mm}${split}${dd} ${hh}:${min}:${ss}`
}

export const elapsedTime = (input?: Date | number | string): string => {
  if (!input) return ''
  const start = new Date(input)
  const now = new Date()

  const diff = Math.floor((now.getTime() - start.getTime()) / 1000)

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
  else if (!bytes) return ''

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}
