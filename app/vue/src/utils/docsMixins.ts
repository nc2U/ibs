import { computed } from 'vue'
import { message } from '@/utils/helper'
import { timeFormat } from '@/utils/baseMixins'
import type { PatchDocs } from '@/store/types/docs'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'

const docStore = useDocs()
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)

const copyCreateDocs = (payload: { docs: number; doc_type: number; issue_project: number }) =>
  docStore.copyDocs(payload)
const deleteDocs = (pk: number, filter: DocsFilter) => docStore.deleteDocs(pk, filter)

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

const is_secret = computed(() => docStore.docs?.is_secret)
const secretTitle = computed(() => (is_secret.value ? '비밀글 해제' : '비밀글로'))
const secretIcon = computed(() => (is_secret.value ? 'lock-open-variant' : 'lock'))

const is_blind = computed(() => docStore.docs?.is_blind)

export const docsManageItems = computed(() => [
  { title: '복사하기', icon: 'content-copy' },
  { title: '이동하기', icon: 'folder-arrow-right' },
  { title: '카테고리변경', icon: 'tag-multiple' },
  { title: secretTitle.value, icon: secretIcon.value },
  {
    title: `블라인드${is_blind.value ? '해제' : '처리'}`,
    icon: `eye${is_blind.value ? '' : '-off'}`,
  },
  { title: '휴지통으로', icon: 'trash-can' },
])

const toSecretDocs = (docs: number, state: boolean, filter: DocsFilter) =>
  patchDocs({
    pk: docs,
    is_secret: !state,
    filter,
  }).then(() =>
    message(
      'info',
      '',
      `이 게시글을 비밀글${!is_secret.value ? '에서 해제' : '로 변경'}하였습니다.`,
    ),
  )

const toBlind = (docs: number, state: boolean, filter: DocsFilter) =>
  patchDocs({
    pk: docs,
    is_blind: !state,
    filter,
  }).then(() =>
    message('info', '', `이 게시글을 블라인드${!is_blind.value ? ' 해제' : ' 처리'}하였습니다.`),
  )

const toTrashCan = async (docs: number, state: boolean, filter: DocsFilter) => {
  if (!state) await deleteDocs(docs, filter)
}

interface ManagePayload {
  issue_project: number | undefined
  doc_type: number | undefined
  type_name: string | undefined
  category: number | undefined
  content: string
  docs: number
  state: boolean
  filter: DocsFilter
  manager: string
}

export const toDocsManage = (fn: number, payload: ManagePayload) => {
  const { issue_project, docs, doc_type, category, content, type_name, manager, state, filter } =
    payload
  if (fn === 11) return copyDocs(issue_project as number, docs, doc_type as number)
  if (fn === 22)
    return moveDocs(docs, doc_type as number, type_name, issue_project, content, manager, filter)
  if (fn === 33) return changeCate(docs, category, filter)
  if (fn === 4) return toSecretDocs(docs, state, filter)
  if (fn === 7) return toBlind(docs, state, filter)
  if (fn === 88) return toTrashCan(docs, state, filter)
}

const copyDocs = (docs: number, doc_type: number, issue_project: number) =>
  copyCreateDocs({ docs, doc_type, issue_project })

const moveDocs = (
  docs: number,
  doc_type: number,
  type_name: string | undefined,
  issue_project: number | undefined,
  org_content: string,
  manager: string,
  filter: DocsFilter,
) => {
  const content = `${org_content}<br /><br /><p>[이 게시물은 ${manager} 님에 의해 ${timeFormat(
    new Date(),
  )} ${type_name} 에서 이동됨]</p>`
  patchDocs({ pk: docs, doc_type, issue_project, content, filter }).then(() =>
    message('success', '', '게시물 이동이 완료되었습니다.'),
  )
}
const changeCate = (docs: number, cate: number | undefined, filter: DocsFilter) => {
  console.log(docs, cate)
  patchDocs({ pk: docs, category: cate, filter }).then(() =>
    message('success', '', '카테고리가 변경되었습니다.'),
  )
}
