export interface Schedule {
  pk: number
  title: string
  all_day: boolean
  start_date: string | null
  end_date: string | null
  start_time: string | null
  end_time: string | null
  creator?: {
    pk: number
    username: string
  }
  created_at?: string
  updated_at?: string
}

export interface Event {
  id?: number
  title: string
  allDay?: boolean
  start?: string
  end?: string
}
