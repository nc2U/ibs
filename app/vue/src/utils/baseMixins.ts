export const numFormat = (val: number | string, n = 0, zero: string | 0 = '-') => {
  const value = Number.isNaN(val) ? 0 : Number(val)
  const parts = value.toFixed(n).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return !value || value === 0 ? zero : parts.join('.')
}

export const cutString = (str = '', len = 0, abb = '...') =>
  str.length > len ? `${str.substring(0, len)}${abb}` : str

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

export const dateFormat = (date: Date | string, split?: string) => {
  const computedDate = typeof date === 'string' ? new Date(date) : date
  const formattedDate = computedDate
    .toLocaleDateString('en-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: 'Asia/Seoul', // Setting timezone to Seoul (KST)
    })
    .replace(/(\d+)\/(\d+)\/(\d+)/, '$3-$1-$2')
  return !split ? formattedDate : formattedDate.replace(/-/g, split)
}

export const getToday = () =>
  new Date(new Date().getTime() + 32400000).toISOString().replace(/T.*$/, '')

export const timeFormat = (date: Date | number | string, short = false, split?: string) => {
  let formattedTime = new Date(+new Date(date) + 32400000)
    .toISOString()
    .replace('T', ' ')
    .replace(/\..*/, '')
  formattedTime = !split ? formattedTime : formattedTime.replace(/-/g, split)
  return !short ? formattedTime : formattedTime.substring(0, 16)
}

export const elapsedTime = (date?: Date | number | string): string => {
  if (!date) return ''
  const start = new Date(date)
  const end = new Date()

  const seconds = Math.floor((end.getTime() - start.getTime()) / 1000)
  if (seconds < 60) return '방금 전'

  const minutes = seconds / 60
  if (minutes < 60) return `${Math.floor(minutes)}분 전`

  const hours = minutes / 60
  if (hours < 24) return `${Math.floor(hours)}시간 전`

  const days = hours / 24
  if (days < 7) return `${Math.floor(days)}일 전`

  const weeks = days / 7
  if (days < 30) return `${Math.floor(weeks)}주일 전`

  const months = days / 30.4375
  if (months < 12) return `${Math.floor(months)}달 전`

  const years = days / 365.25
  return `${Math.floor(years)}년 이상 전`
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
