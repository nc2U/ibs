<script lang="ts" setup>
import { inject, type PropType } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { useRoute, useRouter } from 'vue-router'
import { elapsedTime } from '@/utils/baseMixins'
import { markdownRender } from '@/utils/helper'
import type { Post } from '@/store/types/forum'
import CommentSection from './CommentSection.vue'

const props = defineProps({
  post: { type: Object as PropType<Post>, required: true },
  comments: { type: Array as PropType<any[]>, default: () => [] },
})

const emit = defineEmits(['delete-post', 'like-post', 'blame-post'])

const route = useRoute()
const router = useRouter()

const userInfo = inject<any>('userInfo')

const goList = () =>
  router.push({
    name: '(게시판) - 보기',
    params: { projId: route.params.projId, forumId: props.post.forum },
  })
</script>

<template>
  <template v-if="post">
    <CRow class="py-2">
      <CCol>
        <h5>
          <CBadge v-if="post.is_notice" color="warning" class="mr-2">공지</CBadge>
          {{ post.title }}
        </h5>
      </CCol>
    </CRow>

    <CCard class="mb-4">
      <CCardHeader class="text-body-2 text-muted">
        <router-link to="">{{ post.creator?.username }}</router-link>
        님이 {{ elapsedTime(post.created as string) }} 작성
        <span class="mx-2">|</span>
        조회수 {{ post.hit }}
      </CCardHeader>
      <CCardBody>
        <div v-html="markdownRender(post.content)" class="post-content" />

        <div v-if="post.links?.length || post.files?.length" class="mt-4">
          <v-divider />
          <div v-for="link in post.links" :key="link.pk as number" class="mt-2">
            <v-icon icon="mdi-link-variant" size="small" class="mr-2" />
            <a :href="link.link" target="_blank">{{ link.link }}</a>
          </div>
          <div v-for="file in post.files" :key="file.pk as number" class="mt-2">
            <v-icon icon="mdi-attachment" size="small" class="mr-2" />
            <a :href="file.file" target="_blank">{{ file.file?.split('/').pop() }}</a>
          </div>
        </div>
      </CCardBody>
      <CCardFooter class="text-right">
        <v-btn
          :prepend-icon="post.my_like ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
          size="small"
          :variant="post.my_like ? 'flat' : 'outlined'"
          color="primary"
          class="mr-2"
          @click="emit('like-post', post.pk)"
        >
          {{ post.like }}
        </v-btn>
        <v-btn
          :prepend-icon="post.my_blame ? 'mdi-alert-octagon' : 'mdi-alert-octagon-outline'"
          size="small"
          :variant="post.my_blame ? 'flat' : 'outlined'"
          color="danger"
          @click="emit('blame-post', post.pk)"
        >
          신고
        </v-btn>
      </CCardFooter>
    </CCard>

    <div class="mb-4">
      <CCol class="text-right">
        <v-btn :color="btnLight" size="small" @click="goList">목록으로</v-btn>
        <v-btn
          v-if="userInfo.is_superuser || userInfo?.pk === post.creator?.pk"
          color="success"
          size="small"
          variant="flat"
          class="mr-2"
          :to="{
            name: '(게시판) - 게시물 수정',
            params: { projId: route.params.projId, forumId: post.forum, postId: post.pk },
          }"
        >
          수정
        </v-btn>
        <v-btn
          v-if="userInfo.is_superuser || userInfo?.pk === post.creator?.pk"
          color="warning"
          size="small"
          variant="flat"
          @click="emit('delete-post', post.pk)"
        >
          삭제
        </v-btn>
      </CCol>
    </div>

    <CommentSection
      :post-id="post.pk as number"
      :forum-id="post.forum as number"
      :comments="comments"
    />
  </template>
</template>

<style lang="scss" scoped>
.post-content {
  min-height: 200px;
  line-height: 1.6;
}
</style>
