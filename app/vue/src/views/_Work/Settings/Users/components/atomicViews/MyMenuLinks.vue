<script lang="ts" setup>
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

type MyMenuKey = 'account' | 'project-view' | 'scrap' | 'activity' | 'password'

const props = defineProps<{
  current: MyMenuKey
}>()

const accStore = useAccount()

const menuItems: Array<{
  key: MyMenuKey
  name: string
  routeName: string
  icon: string
  iconColor: string
}> = [
  {
    key: 'account',
    name: '내 계정',
    routeName: '사용자 - 내 계정',
    icon: 'mdi-account-cog-outline',
    iconColor: 'primary',
  },
  {
    key: 'project-view',
    name: '내 워크스페이스 목록',
    routeName: '사용자 - 프로젝트 보기',
    icon: 'mdi-chart-box-multiple-outline',
    iconColor: 'info',
  },
  {
    key: 'scrap',
    name: '내 스크랩',
    routeName: '사용자 - 내 스크랩',
    icon: 'mdi-bookmark-multiple-outline',
    iconColor: 'success',
  },
  {
    key: 'activity',
    name: '내 작성 활동',
    routeName: '사용자 - 내 활동',
    icon: 'mdi-file-document-edit-outline',
    iconColor: 'secondary',
  },
  {
    key: 'password',
    name: '비밀번호 변경',
    routeName: '사용자 - 비밀번호 변경',
    icon: 'mdi-key-outline',
    iconColor: 'amber',
  },
]

const visibleItems = computed(() => menuItems.filter(item => item.key !== props.current))

const handleItemClick = (key: MyMenuKey) => {
  if (key === 'project-view') {
    accStore.user = accStore.userInfo
  }
}
</script>

<template>
  <CCol class="text-end form-text">
    <span v-for="item in visibleItems" :key="item.key" class="me-2">
      <TextButton
        :name="item.name"
        :to="{ name: item.routeName }"
        :icon="item.icon"
        :icon-color="item.iconColor"
        @click="handleItemClick(item.key)"
      />
    </span>
  </CCol>
</template>
