<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import type { Post } from '@/store/types/forum'
import { useRoute, useRouter } from 'vue-router'
import { elapsedTime, humanizeFileSize } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import CommentSection from './CommentSection.vue'
import MDContent from '@/components/OtherParts/MDContent.vue'
import PostContent from '@/components/OtherParts/PostContent.vue'

const props = defineProps({
  post: { type: Object as PropType<Post>, required: true },
  comments: { type: Array as PropType<any[]>, default: () => [] },
})

const emit = defineEmits(['delete-post', 'like-post', 'blame-post'])

const route = useRoute()
const router = useRouter()

const { can, PERM } = usePerms()
const canForumUpdate = computed(() => {
  if (can(PERM.FORUM_UPDATE)) return true
  if (can(PERM.FORUM_OWN_UPDATE)) return props.post.creator?.pk === userInfo.value?.pk
  return false
})

const canForumDelete = computed(() => {
  if (can(PERM.FORUM_DELETE)) return true
  if (can(PERM.FORUM_OWN_DELETE)) return props.post?.creator?.pk === userInfo.value?.pk
  return false
})

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
</script>

<template>
  <template v-if="post">
    <CRow class="py-2">
      <CCol>
        <h4 class="font-weight-bold">
          <v-chip v-if="post.is_notice" color="warning" size="small" class="mr-2">공지</v-chip>
          {{ post.title }}
        </h4>
      </CCol>
    </CRow>

    <v-card class="mb-6 card-white" flat border>
      <!-- v-card로 변경, mb-6으로 하단 간격, flat border 추가 -->
      <v-card-text class="py-2">
        <!-- CCardHeader 대신 v-card-text 사용 -->
        <v-row no-gutters align="center" class="text-caption text-grey">
          <v-col cols="auto" class="mr-3">
            <v-icon icon="mdi-account-circle-outline" size="small" class="mr-1" />
            <router-link
              :to="{
                name: '(게시판) - 보기',
                params: { projId: route.params.projId, forumId: post.forum },
              }"
              class="text-decoration-none text-grey"
            >
              {{ post.creator?.username }}
            </router-link>
          </v-col>
          <v-col cols="auto" class="mr-3">
            <v-icon icon="mdi-clock-outline" size="small" class="mr-1" />
            {{ elapsedTime(post.created as string) }}
          </v-col>
          <v-col cols="auto">
            <v-icon icon="mdi-eye-outline" size="small" class="mr-1" />
            조회수 {{ post.hit }}
          </v-col>
        </v-row>
      </v-card-text>

      <v-divider />

      <v-card-text>
        <PostContent :content="post.content" />

        <div v-if="post.links?.length || post.files?.length" class="mt-6 pt-6 files-section">
          <!-- 상단 간격 조정 -->
          <h6 v-if="post.files?.length" class="mb-2">첨부 파일</h6>
          <div v-for="file in post.files" :key="file.pk as number" class="mb-2">
            <v-icon icon="mdi-attachment" size="small" class="mr-2" />
            <a :href="file.file" target="_blank">{{ file.file_name }}</a>
            <span class="ml-2 text-muted">{{ humanizeFileSize(file.file_size) }}</span>
          </div>
          <h6 v-if="post.links?.length" class="text-h6 mt-4 mb-2">관련 링크</h6>
          <div v-for="link in post.links" :key="link.pk as number" class="mb-2">
            <v-icon icon="mdi-link-variant" size="small" class="mr-2" />
            <a :href="link.link" target="_blank">{{ link.link }}</a>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="justify-end py-2 border-top">
        <v-btn
          :prepend-icon="post.my_like ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
          size="small"
          :variant="post.my_like ? 'flat' : 'tonal'"
          color="primary"
          class="mr-2"
          @click="emit('like-post', post.pk)"
        >
          {{ post.like }}
        </v-btn>
        <v-btn
          :prepend-icon="post.my_blame ? 'mdi-alert-octagon' : 'mdi-alert-octagon-outline'"
          size="small"
          :variant="post.my_blame ? 'flat' : 'tonal'"
          color="error"
          @click="emit('blame-post', post.pk)"
        >
          신고
        </v-btn>
      </v-card-actions>
    </v-card>

    <div class="text-right mb-6">
      <!-- 하단 간격 조정 -->
      <v-btn color="light" variant="flat" size="small" class="mr-2" @click="router.back()">
        목록으로
      </v-btn>
      <v-btn
        v-if="userInfo?.is_superuser || userInfo?.pk === post.creator?.pk"
        color="success"
        size="small"
        class="mr-2"
        :disabled="!canForumUpdate"
        :to="{
          name: '(게시판) - 게시물 수정',
          params: { projId: route.params.projId, forumId: post.forum, postId: post.pk },
        }"
      >
        <v-icon icon="mdi-pencil" size="small" class="mr-1" />
        수정
      </v-btn>
      <v-btn
        v-if="userInfo?.is_superuser || userInfo?.pk === post.creator?.pk"
        color="warning"
        size="small"
        :disabled="!canForumDelete"
        @click="emit('delete-post', post.pk)"
      >
        <v-icon icon="mdi-trash-can-outline" size="small" class="mr-1" />
        삭제
      </v-btn>
    </div>

    <CommentSection
      :post-id="post.pk as number"
      :forum-id="post.forum as number"
      :comments="comments"
    />
  </template>
</template>
