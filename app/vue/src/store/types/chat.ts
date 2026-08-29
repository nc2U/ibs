export interface ChatUser {
  pk: number
  username: string
  email?: string
}

export type ChatRoomType = 'channel' | 'group' | 'direct'
export type ChatMessageType = 'text' | 'image' | 'file' | 'issue' | 'meeting' | 'approval' | 'system'

export interface ChatLastMessage {
  id: number
  sender_name: string
  message_type: ChatMessageType
  content: string
  created: string
}

export interface ChatRoom {
  id: number
  project?: number | null
  project_name?: string | null
  room_type: ChatRoomType
  title: string
  description: string
  created_by?: number | null
  created: string
  updated: string
  member_count: number
  members: ChatUser[]
  last_message?: ChatLastMessage | null
  unread_count: number
  is_pinned: boolean
  is_muted: boolean
}

export interface ChatMessage {
  id: number
  room: number
  sender?: ChatUser | null
  message_type: ChatMessageType
  content: string
  file?: string | null
  file_name?: string
  file_size?: number
  ref_id?: number | null
  ref_title?: string
  ref_sub?: string
  reply_to?: number | null
  reply_to_detail?: {
    id: number
    sender_name: string
    content: string
    message_type: ChatMessageType
  } | null
  created: string
}
