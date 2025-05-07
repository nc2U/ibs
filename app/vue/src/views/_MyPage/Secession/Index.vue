<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/_MyPage/_menu/headermixin'
import { message } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PasswordCheck from '@/views/_MyPage/Secession/components/PasswordCheck.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const refConfirmModal = ref()
const refPassCheck = ref()

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const passChecked = computed(() => accStore.passChecked)

const checkPassword = (payload: { email: string; password: string }) =>
  accStore.checkPassword(payload)
const patchProfile = (payload: { pk: number; form: FormData }) => accStore.patchProfile(payload)

const removeConfirm = () => refConfirmModal.value.callModal('', '', '', 'danger')

const modalAction = () => {
  const email = userInfo.value?.email ?? ''
  checkPassword({ email, password: refPassCheck.value.getPass() })
  refConfirmModal.value.close()
}

watch(passChecked, nVal => {
  if (nVal) {
    removeUser()
    refPassCheck.value.passReset()
    accStore.passChecked = false
  }
})

const removeUser = () => {
  const pk = userInfo.value?.profile?.pk as number
  const form = new FormData()
  form.append('is_active', 'false')
  console.log(userInfo.value)
  patchProfile({ pk, form })
  message('danger', '', '사용자 계정이 삭제(비활성화) 되었습니다.', 5000)
}
</script>

<template>
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <PasswordCheck
      ref="refPassCheck"
      :username="userInfo?.username"
      @remove-confirm="removeConfirm"
    />
  </ContentBody>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 멤버 영구 탈퇴</template>
    <template #default>
      정말 멤버 탈퇴를 진행하시겠습니까?<br />
      탈퇴한 회원정보는 복구할 수 없으므로 신중히 선택하여 주십시요. <br />
      획인을 누르면 탈퇴가 진행됩니다.
    </template>
    <template #footer>
      <v-btn color="danger" @click="modalAction"> 확인</v-btn>
    </template>
  </ConfirmModal>
</template>
