import { computed } from 'vue'
import { message } from '@/utils/helper'
import { timeFormat } from '@/utils/baseMixins'
import type { PatchPost } from '@/store/types/board'
import { type PostFilter, useBoard } from '@/store/pinia/board'

const boardStore = useBoard()
const patchPost = (payload: PatchPost & { filter: PostFilter }) => boardStore.patchPost(payload)
const patchPostLike = (pk: number) => boardStore.patchPostLike(pk)
const patchPostBlame = (pk: number) => boardStore.patchPostBlame(pk)

const patchCommentLike = (pk: number, post: number, page?: number) =>
  boardStore.patchCommentLike(pk, post, page)
const patchCommentBlame = (pk: number, post: number, page?: number) =>
  boardStore.patchCommentBlame(pk, post, page)
const copyCreatePost = (payload: { post: number; board: number }) => boardStore.copyPost(payload)
const deletePost = (pk: number, filter: PostFilter) => boardStore.deletePost(pk, filter)

export const toPrint = (title: string) => {
  // Clone the specific area to be printed
  const printContent: any = document.getElementById('print-area')?.cloneNode(true)

  // Create a new window for printing
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.open()

    // Add the cloned content to the new window
    printWindow.document.write(`<html><head><title>${title}</title></head><body>`)
    printWindow.document.write(printContent?.innerHTML)
    printWindow.document.write('</body></html>')

    // Close the document for writing
    printWindow.document.close()

    // Print the new window
    printWindow.print()
    // Close the new window after printing
    printWindow.close()
  }
}

export const toPostLike = (pk: number) => patchPostLike(pk)

export const toPostBlame = (pk: number) => patchPostBlame(pk)

export const toCommentLike = (pk: number, post: number, page = 1) =>
  patchCommentLike(pk, post, page)

export const toCommentBlame = (pk: number, post: number, page = 1) =>
  patchCommentBlame(pk, post, page)

const is_secret = computed(() => boardStore.post?.is_secret)
const secretTitle = computed(() => (is_secret.value ? '비밀글 해제' : '비밀글로'))
const secretIcon = computed(() => (is_secret.value ? 'lock-open-variant' : 'lock'))

const is_hide_cmt = computed(() => boardStore.post?.is_hide_comment)
const hideCmtTitle = computed(() => (is_hide_cmt.value ? '댓글숨김 해제' : '댓글숨김'))

const is_notice = computed(() => boardStore.post?.is_notice)
const notiTitle = computed(() => (is_notice.value ? '공지내림' : '공지올림'))

const is_blind = computed(() => boardStore.post?.is_blind)

export const postManageItems = computed(() => [
  { title: '복사하기', icon: 'content-copy' },
  { title: '이동하기', icon: 'folder-arrow-right' },
  { title: '카테고리변경', icon: 'tag-multiple' },
  { title: secretTitle.value, icon: secretIcon.value },
  { title: hideCmtTitle.value, icon: `comment${is_hide_cmt.value ? '' : '-off'}` },
  { title: notiTitle.value, icon: `bullhorn-variant${is_notice.value ? '-outline' : ''}` },
  {
    title: `블라인드${is_blind.value ? '해제' : '처리'}`,
    icon: `eye${is_blind.value ? '' : '-off'}`,
  },
  { title: '휴지통으로', icon: 'trash-can' },
])

const toSecretPost = (post: number, state: boolean, filter: PostFilter) =>
  patchPost({
    pk: post,
    is_secret: !state,
    filter,
  }).then(() =>
    message(
      'info',
      '',
      `이 게시글을 비밀글${!is_secret.value ? '에서 해제' : '로 변경'}하였습니다.`,
    ),
  )

const hideComments = (post: number, state: boolean, filter: PostFilter) =>
  patchPost({
    pk: post,
    is_hide_comment: !state,
    filter,
  }).then(() =>
    message(
      'info',
      '',
      `이 게시물의 댓글을 숨김${!is_secret.value ? ' 해제' : ' 처리'}하였습니다.`,
    ),
  )

const toNoticeUp = (post: number, state: boolean, filter: PostFilter) =>
  patchPost({
    pk: post,
    is_notice: !state,
    filter,
  }).then(() =>
    message(
      'info',
      '',
      `이 게시글을 공지글${!is_notice.value ? '에서 해제' : '로 등록'}하였습니다.`,
    ),
  )

const toBlind = (post: number, state: boolean, filter: PostFilter) =>
  patchPost({
    pk: post,
    is_blind: !state,
    filter,
  }).then(() =>
    message('info', '', `이 게시글을 블라인드${!is_blind.value ? ' 해제' : ' 처리'}하였습니다.`),
  )

const toTrashCan = async (post: number, state: boolean, filter: PostFilter) => {
  if (!state) await deletePost(post, filter)
}

interface ManagePayload {
  board: number | undefined
  board_name: string | undefined
  category: number | undefined
  content: string
  post: number
  state: boolean
  filter: PostFilter
  manager: string
}

export const toPostManage = (fn: number, payload: ManagePayload) => {
  const { post, board, category, content, board_name, manager, state, filter } = payload
  if (fn === 11) return copyPost(post, board as number)
  if (fn === 22) return movePost(post, board as number, board_name, content, manager, filter)
  if (fn === 33) return changeCate(post, category, filter)
  if (fn === 4) return toSecretPost(post, state, filter)
  if (fn === 5) return hideComments(post, state, filter)
  if (fn === 6) return toNoticeUp(post, state, filter)
  if (fn === 7) return toBlind(post, state, filter)
  if (fn === 88) return toTrashCan(post, state, filter)
}

const copyPost = (post: number, board: number) => copyCreatePost({ post, board })

const movePost = (
  post: number,
  board: number,
  board_name: string | undefined,
  org_content: string,
  manager: string,
  filter: PostFilter,
) => {
  const content = `${org_content}<br /><br /><p>[이 게시물은 ${manager} 님에 의해 ${timeFormat(
    new Date(),
  )} ${board_name} 에서 이동됨]</p>`
  patchPost({ pk: post, board, content, filter }).then(() =>
    message('success', '', '게시물 이동이 완료되었습니다.'),
  )
}
const changeCate = (post: number, cate: number | undefined, filter: PostFilter) => {
  console.log(post, cate)
  patchPost({ pk: post, category: cate, filter }).then(() =>
    message('success', '', '카테고리가 변경되었습니다.'),
  )
}
