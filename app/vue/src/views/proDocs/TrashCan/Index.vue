<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/proDocs/_menu/headermixin1'
import { usePerms } from '@/composables/usePerms.ts'
import { useDocs } from '@/store/pinia/docs'
import { useRoute, useRouter } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProDocsAuthGuard from '@/components/AuthGuard/ProDocsAuthGuard.vue'
import TrashDocsList from './components/TrashDocsList.vue'
import TrashDocsDetail from './components/TrashDocsDetail.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const mainViewName = '문서 휴지통'
const page = ref<number>(1)

const { canGlobal, PERM } = usePerms()
const canReadTrash = computed(() => canGlobal(PERM.DOCS_READ))

const docStore = useDocs()
const trashDocs = computed(() => docStore.trashDocs)
const trashDocsList = computed(() => docStore.trashDocsList)
const trashDocsCount = computed(() => docStore.trashDocsCount)

const route = useRoute()
const router = useRouter()

const docsId = computed(() => (route.params.docsId ? Number(route.params.docsId) : null))

watch(
  [docsId, canReadTrash],
  async ([id, allowed]) => {
    if (id && !Number.isNaN(id) && allowed) {
      await docStore.fetchTrashDocs(id)
    } else if (!id) {
      docStore.removeTrashDocs()
    }
  },
  { immediate: true },
)

const pageSelect = async (p: number) => {
  if (!canReadTrash.value) return
  page.value = p
  await docStore.fetchTrashDocsList(p)
}

const restoreId = ref<number | null>(null)
const refRestoreModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const callRestoreDocs = (pk: number) => {
  restoreId.value = pk
  refRestoreModal.value?.callModal(
    '문서 복원 확인',
    '이 문서를 휴지통에서 복원하시겠습니까?',
    'mdi-delete-restore',
    'success',
    '삭제 복원',
    'success',
  )
}

const resModalAction = async () => {
  if (!restoreId.value) return
  const nextPage = trashDocsList.value.length <= 1 && page.value > 1 ? page.value - 1 : page.value
  const ok = await docStore.restoreDocs(restoreId.value, nextPage)
  if (!ok) return
  page.value = nextPage
  restoreId.value = null
  refRestoreModal.value?.close()
  if (route.name !== mainViewName) {
    await router.replace({ name: mainViewName })
  }
}

const deleteId = ref<number | null>(null)
const refDeleteModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const callDeleteDocs = (pk: number) => {
  deleteId.value = pk
  refDeleteModal.value?.callModal(
    '영구 삭제 확인',
    '완전 삭제 후에는 복원할 수 없습니다. 이 문서를 영구 삭제하시겠습니까?',
    'mdi-delete-forever-outline',
    'warning',
    '완전 삭제',
    'danger',
  )
}

const delModalAction = async () => {
  if (!deleteId.value) return
  const nextPage = trashDocsList.value.length <= 1 && page.value > 1 ? page.value - 1 : page.value
  const ok = await docStore.deleteTrashDocs(deleteId.value, nextPage)
  if (!ok) return
  page.value = nextPage
  deleteId.value = null
  refDeleteModal.value?.close()
  if (route.name !== mainViewName) {
    await router.replace({ name: mainViewName })
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    if (canReadTrash.value) await docStore.fetchTrashDocsList(page.value)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <ProDocsAuthGuard global>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

    <ContentBody>
      <CCardBody class="pb-5">
        <div v-if="route.name === mainViewName" class="pt-3">
          <TrashDocsList
            :trash-docs-list="trashDocsList"
            :trash-docs-count="trashDocsCount"
            :view-route="mainViewName"
            :page="page"
            @page-select="pageSelect"
            @restore-docs="callRestoreDocs"
            @delete-docs="callDeleteDocs"
          />
        </div>

        <div v-else-if="String(route.name ?? '').includes('보기')" class="pt-3">
          <TrashDocsDetail
            :docs="trashDocs"
            :view-route="mainViewName"
            @restore-docs="callRestoreDocs"
            @delete-docs="callDeleteDocs"
          />
        </div>
      </CCardBody>
    </ContentBody>

    <ConfirmModal ref="refRestoreModal" checked @confirm-func="resModalAction" />
    <ConfirmModal ref="refDeleteModal" @confirm-func="delModalAction" />
  </ProDocsAuthGuard>
</template>
