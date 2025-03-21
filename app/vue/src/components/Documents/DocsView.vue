<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import { ref, computed, watch, inject, onBeforeMount, onMounted } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'
import { type Docs } from '@/store/types/docs'
import type { User } from '@/store/types/accounts'
import type { Company } from '@/store/types/settings'
import { toPrint, docsManageItems, toDocsManage } from '@/utils/docsMixins'
import sanitizeHtml from 'sanitize-html'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TypeListModal from '@/components/Documents/components/TypeListModal.vue'
import CateListModal from '@/components/Documents/components/CateListModal.vue'
import PostInfo from '@/components/OtherParts/PostInfo.vue'

const props = defineProps({
  typeNum: { type: Number, default: 1 },
  heatedPage: { type: Array as PropType<number[]>, default: () => [] },
  reOrder: { type: Boolean, default: false },
  category: { type: Number, default: undefined },
  docs: { type: Object as PropType<Docs>, default: null },
  viewRoute: { type: String, required: true },
  currPage: { type: Number, required: true },
  writeAuth: { type: Boolean, default: true },
  docsFilter: { type: Object as PropType<DocsFilter>, default: null },
})

const emit = defineEmits(['docs-hit', 'link-hit', 'file-hit', 'docs-scrape', 'docs-renewal'])

const refDelModal = ref()
const refAlertModal = ref()
const refTypeListModal = ref()
const isCopy = ref(false)
const refCateListModal = ref()
const refTrashModal = ref()

const userInfo = inject<ComputedRef<User>>('userInfo')
const editAuth = computed(
  () => userInfo?.value?.is_superuser || props.docs.user?.pk === userInfo?.value?.pk,
)

const prev = ref<number | null>()
const next = ref<number | null>()

const company = inject<ComputedRef<Company>>('company')

const sortName = computed(() => props.docs?.proj_name || '본사 문서')
const docsId = computed(() => Number(route.params.docsId))

const docStore = useDocs()
const docTypeList = computed(() => docStore.docTypeList)
const categoryList = computed(() => docStore.categoryList)
const getDocsNav = computed(() => docStore.getDocsNav)

const getPrev = (pk: number) => getDocsNav.value.filter(p => p.pk === pk).map(p => p.prev_pk)[0]
const getNext = (pk: number) => getDocsNav.value.filter(p => p.pk === pk).map(p => p.next_pk)[0]

const linkHitUp = async (pk: number) => emit('link-hit', pk)
const fileHitUp = async (pk: number) => emit('file-hit', pk)

const [route, router] = [useRoute(), useRouter()]

const sendUrl = `${window.location.host}${route.fullPath}`

const shareFacebook = () => window.open(`https://facebook.com/share/share.php?u=${sendUrl}`)
const shareTwitter = () => window.open(`https://twitter.com/intent/tweet?text=&url=${sendUrl}`)
const shareKakaoTalk = () => {
  // 카카오링크 버튼 생성
  ;(window as any).Kakao.Share.createDefaultButton({
    container: '#kakaotalk-sharing-btn',
    objectType: 'feed',
    content: {
      title: company?.value.name,
      description: `#공지사항 #${props.docs?.title}`,
      imageUrl: 'https://brdnc.co.kr/static/dist/img/icons/ms-icon-310x310.png',
      link: {
        // [내 애플리케이션] > [플랫폼] 에서 등록한 사이트 도메인과 일치해야 함
        mobileWebUrl: sendUrl,
        webUrl: sendUrl,
      },
    },
    social: {
      likeCount: props.docs.like,
      // sharedCount: 45,
    },
    buttons: [
      {
        title: '웹으로 보기',
        link: {
          mobileWebUrl: sendUrl,
          webUrl: sendUrl,
        },
      },
      {
        title: '앱으로 보기',
        link: {
          mobileWebUrl: sendUrl,
          webUrl: sendUrl,
        },
      },
    ],
  })
}

const toScrape = () => {
  if (props.docs.my_scrape) refAlertModal.value.callModal('', '이미 이 포스트를 스크랩 하였습니다.')
  else emit('docs-scrape', props.docs.pk)
}

const toManage = (fn: number, el?: { nType?: number; nProj?: number; nCate?: number }) => {
  const docs = props.docs.pk
  let state: boolean = false
  if (fn < 4) {
    if (fn === 1) {
      isCopy.value = true
      refTypeListModal.value.callModal()
    } else if (fn === 2) {
      isCopy.value = false
      refTypeListModal.value.callModal()
    } else if (fn === 3) {
      refCateListModal.value.callModal()
    }
  } else {
    if (fn === 4)
      state = props.docs.is_secret // is_secret
    else if (fn === 7)
      state = props.docs.is_blind // is_blind
    else if (fn === 8)
      refTrashModal.value.callModal() // deleted confirm
    else if (fn === 88) {
      // soft delete
      state = !!props.docs.deleted // is_deleted
      refTrashModal.value.close()
      router.replace({ name: props.viewRoute })
    }
    const payload = {
      doc_type: el?.nType,
      type_name: props.docs.type_name,
      issue_project: el?.nProj,
      category: el?.nCate,
      content: props.docs?.content ?? '',
      docs: docs as number,
      state,
      filter: props.docsFilter,
      manager: userInfo?.value.username as string,
    }
    toDocsManage(fn, payload)
  }
}

const copyDocs = (nType?: number, nProj?: number) => toManage(11, { nType, nProj })
const moveDocs = (nType?: number, nProj?: number) => toManage(22, { nType, nProj })
const changeCate = (nCate?: number) => toManage(33, { nCate })

const getFileName = (file: string) => {
  if (file) return decodeURI(file.split('/').slice(-1)[0])
  else return
}

const toEdit = () => {
  router.push({
    name: `${props.viewRoute} - 수정`,
    params: { docsId: props.docs?.pk },
  })
}

const deleteConfirm = () => refTrashModal.value.callModal()

const toDelete = () => {
  if (userInfo?.value.is_superuser) toManage(88)
  refDelModal.value.close()
}

watch(
  () => getDocsNav.value,
  () => {
    if (docsId.value) {
      prev.value = getPrev(docsId.value)
      next.value = getNext(docsId.value)
    }
  },
)

onBeforeRouteUpdate((to, from) => {
  const toRoute = (to.name ?? '') as string
  if (toRoute.includes('보기')) {
    const fromDocsId = from.params.docsId ? Number(from.params.docsId) : null
    const toDocsId = to.params.docsId ? Number(to.params.docsId) : null

    const last = getDocsNav.value.length - 1
    const getLast = getDocsNav.value[last]
    if (toDocsId && getLast.pk === fromDocsId && getLast.prev_pk === toDocsId)
      // 다음 페이지 목록으로
      emit('docs-renewal', props.currPage + 1)

    const getFirst = getDocsNav.value[0]
    if (toDocsId && getFirst.pk === fromDocsId && getFirst.next_pk === toDocsId)
      // 이전 페이지 목록으로
      emit('docs-renewal', props.currPage - 1)

    if (toDocsId) {
      prev.value = getPrev(toDocsId)
      next.value = getNext(toDocsId)
    }
  }
})

onBeforeMount(() => {
  if (docsId.value) {
    docStore.fetchDocs(docsId.value)
    prev.value = getPrev(docsId.value)
    next.value = getNext(docsId.value)
  }
})

onMounted(() => {
  if (docsId.value && !props.heatedPage?.includes(docsId.value)) {
    emit('docs-hit', docsId.value)
  }
})
</script>

<template>
  <div v-if="docs" class="m-0 p-0">
    <CRow class="mt-5">
      <CCol md="8">
        <h5>
          <v-icon v-if="docs.is_notice" icon="mdi-bullhorn" size="sm" color="blue-grey-darken-1" />
          {{ docs.title }}
        </h5>
      </CCol>
      <CCol v-if="docs.cate_name" class="pt-1 text-right">
        <span>[{{ sortName }}] [{{ docs.cate_name }}]</span>
      </CCol>
    </CRow>

    <v-divider />

    <PostInfo :docs="docs" />

    <!--    <CRow class="text-blue-grey mb-5">-->
    <!--      <CCol>-->
    <!--        <small class="mr-3">작성자 : {{ docs.user?.username }}</small>-->
    <!--        <small class="mr-2">-->
    <!--          <v-icon icon="mdi-eye" size="sm" />-->
    <!--          <span class="ml-1">{{ docs.hit }}</span>-->
    <!--        </small>-->
    <!--        <small class="mr-2">-->
    <!--          <v-icon icon="mdi-heart" size="sm" />-->
    <!--          <span class="ml-1">{{ docs.like }}</span>-->
    <!--        </small>-->
    <!--        <small class="mr-2 text-btn" @click="toPrint(docs.title)">-->
    <!--          <v-icon icon="mdi-printer" size="sm" />-->
    <!--          <span class="ml-1">프린트</span>-->
    <!--        </small>-->
    <!--      </CCol>-->

    <!--      <CCol class="text-right" md="3">-->
    <!--        <small>-->
    <!--          <v-icon icon="mdi-calendar-clock" size="small" />-->
    <!--          <span class="ml-2">{{ timeFormat(docs.created ?? '') }}</span>-->
    <!--        </small>-->
    <!--      </CCol>-->
    <!--    </CRow>-->

    <CRow v-if="docs.is_secret">
      <CCol>
        <CAlert color="info">
          이 글은 비밀글입니다. 작성자 본인과 관리자만 열람할 수 있습니다.
        </CAlert>
      </CCol>
    </CRow>

    <CRow v-if="docs.is_blind">
      <CCol>
        <CAlert color="danger">
          이 글은 블라인드 처리된 글입니다. 작성자 본인과 관리자만 확인이 가능합니다.
        </CAlert>
      </CCol>
    </CRow>

    <div v-show="!docs.is_blind || userInfo?.pk === docs.user?.pk || userInfo?.is_superuser">
      <CRow class="py-2 justify-content-between">
        <CCol md="7" lg="6" xl="5">
          <table v-if="typeNum !== 1 && docs.execution_date" class="table table-bordered mt-2 mb-3">
            <tbody>
              <tr v-if="docs.lawsuit">
                <td class="p-2 bg-blue-grey-lighten-4 text-center">관련사건</td>
                <td class="p-2">
                  <router-link
                    :to="{ name: '현장 소송 사건 - 보기', params: { caseId: docs.lawsuit } }"
                  >
                    {{ docs.lawsuit_name }}
                  </router-link>
                </td>
              </tr>
              <tr>
                <td class="p-2 bg-blue-grey-lighten-4 text-center">발행일자</td>
                <td class="p-2">{{ docs.execution_date }}</td>
              </tr>
            </tbody>
          </table>
        </CCol>

        <CCol md="7" lg="6" xl="5">
          <CRow v-if="!!docs.links && docs.links.length" class="mb-3">
            <CCol>
              <CListGroup>
                <CListGroupItem>Link</CListGroupItem>
                <CListGroupItem
                  v-for="l in docs.links"
                  :key="l.pk"
                  class="d-flex justify-content-between align-items-center"
                >
                  <a :href="l.link" target="_blank" @click="linkHitUp(l.pk as number)">
                    {{ cutString(l.link, 45) }}
                  </a>
                  <small>
                    조회 수 :
                    <CBadge color="info" shape="rounded-pill">
                      {{ l.hit }}
                    </CBadge>
                  </small>
                </CListGroupItem>
              </CListGroup>
            </CCol>
          </CRow>

          <CRow v-if="docs.files && docs.files.length">
            <CCol>
              <CListGroup>
                <CListGroupItem>File</CListGroupItem>
                <CListGroupItem
                  v-for="f in docs.files"
                  :key="f.pk"
                  class="d-flex justify-content-between align-items-center"
                >
                  <a :href="f.file" target="_blank" @click="fileHitUp(f.pk as number)">
                    {{ cutString(getFileName(f.file ?? ''), 45) }}
                  </a>
                  <small>
                    다운로드 :
                    <CBadge color="success" shape="rounded-pill">
                      {{ f.hit }}
                    </CBadge>
                  </small>
                </CListGroupItem>
              </CListGroup>
            </CCol>
          </CRow>
        </CCol>
      </CRow>

      <CRow class="my-5 p-3" id="print-area">
        <CCol class="pb-5">
          <div v-html="sanitizeHtml(docs.content)" />
        </CCol>
      </CRow>
    </div>

    <CRow class="my-3 px-3">
      <CCol class="text-grey-darken-1 pt-2 social">
        <a
          id="kakaotalk-sharing-btn"
          href="javascript:void(0)"
          @click="shareKakaoTalk"
          class="mr-2"
        >
          <img
            src="https://developers.kakao.com/assets/img/about/logos/kakaotalksharing/kakaotalk_sharing_btn_medium.png"
            alt="카카오톡 공유 보내기 버튼"
            width="20px;"
          />
        </a>
        <v-icon icon="mdi-facebook" class="mr-2" @click="shareFacebook" />
        <v-icon icon="mdi-twitter" class="mr-2" @click="shareTwitter" />
      </CCol>
      <CCol class="text-right">
        <v-btn
          variant="tonal"
          :color="docs.my_scrape ? 'primary' : ''"
          size="small"
          :rounded="0"
          class="mr-1"
          @click="toScrape"
        >
          스크랩 {{ docs.scrape ? `+${docs.scrape}` : '' }}
        </v-btn>
        <v-btn
          v-if="userInfo?.is_superuser"
          prepend-icon="mdi-cog"
          variant="tonal"
          size="small"
          :rounded="0"
        >
          관리
          <v-menu activator="parent" open-on-hover>
            <v-list density="compact">
              <v-list-item
                v-for="(item, index) in docsManageItems"
                :key="index"
                :value="index"
                @click="toManage(index + 1)"
              >
                <v-list-item-title style="font-size: 0.9em">
                  <v-icon :icon="`mdi-${item.icon}`" size="sm" />
                  {{ item.title }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-btn>
      </CCol>
    </CRow>

    <v-divider />

    <CRow class="py-2">
      <CCol>
        <CButtonGroup role="group">
          <CButton v-if="editAuth" color="success" :disabled="!writeAuth" @click="toEdit">
            수정
          </CButton>
          <CButton v-if="editAuth" color="danger" :disabled="!writeAuth" @click="deleteConfirm">
            삭제
          </CButton>
          <CButton color="secondary" @click="router.push({ name: `${viewRoute}` })"> 목록</CButton>
          <CButton
            color="light"
            :disabled="!prev || reOrder"
            @click="
              router.push({
                name: `${viewRoute} - 보기`,
                params: { docsId: prev },
              })
            "
          >
            이전
          </CButton>
          <CButton
            color="light"
            :disabled="!next || reOrder"
            @click="
              router.push({
                name: `${viewRoute} - 보기`,
                params: { docsId: next },
              })
            "
          >
            다음
          </CButton>
        </CButtonGroup>
      </CCol>
      <CCol class="text-right">
        <CButton
          v-if="writeAuth"
          color="primary"
          @click="router.push({ name: `${viewRoute} - 작성` })"
        >
          신규등록
        </CButton>
      </CCol>
    </CRow>
  </div>

  <AlertModal ref="refAlertModal" />

  <TypeListModal
    ref="refTypeListModal"
    :now-type="docs?.doc_type ?? undefined"
    :doc-type-list="docTypeList"
    :is-copy="isCopy"
    @copy-docs="copyDocs"
    @move-docs="moveDocs"
  />
  <!--    :now-project="docs?.project ?? undefined"-->

  <CateListModal
    ref="refCateListModal"
    :now-cate="docs?.category ?? undefined"
    :category-list="categoryList"
    @change-cate="changeCate"
  />

  <ConfirmModal ref="refTrashModal">
    <template #header>알림</template>
    <template #default>이 게시물을 휴지통으로 삭제 하시겠습니까?</template>
    <template #footer>
      <CButton color="danger" @click="toManage(88)">삭제</CButton>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refDelModal">
    <template #header>알림</template>
    <template #default>한번 삭제한 자료는 복구할 수 없습니다. 정말 삭제하시겠습니까?</template>
    <template #footer>
      <CButton color="danger" @click="toDelete">삭제</CButton>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.social i {
  cursor: pointer;
}

.social i:hover {
  color: darkslateblue;
}
</style>
