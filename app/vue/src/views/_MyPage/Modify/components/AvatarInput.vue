<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue'
import CropperModal from './CropperModal.vue'

const props = withDefaults(
  defineProps<{
    image: string | File
    filename?: string
  }>(),
  {
    filename: 'profile',
  },
)

const emit = defineEmits(['trans-profile-form'])

const imgSource = ref<string | File>('') // 화면에 표시되는 이미지 소스

const modalImg = ref()
const cropModal = ref()

const browse = () => {
  const fu = document.getElementById('file')
  if (!!fu) fu.click()
}

const loadFile = (payload: Event) => {
  // 이미지 선택 시 동작 -> 원본이미지를 데이터화해서 cropperModal로 로드
  const inputEl = payload.target as HTMLInputElement
  if (inputEl.files) {
    const img = inputEl.files[0] // 원본 이미지
    const reader = new FileReader()
    reader.readAsDataURL(img) // 주소 데이터화
    reader.onload = e => {
      modalImg.value = e.target?.result // 크로퍼에 할당
      if (!!modalImg.value) cropModal.value.visible = true
    }
  }
}

const transAvatarInput = (img: File) => {
  // cropperModal에서 이미지 크롭(submit) 시 동작
  emit('trans-profile-form', img) // 크롭된 이미지
  const reader = new FileReader()
  reader.readAsDataURL(img) // 주소 데이터화
  reader.onload = e => (imgSource.value = String(e.target?.result)) // 화면 표시 이미지 변경
}

const delModalImg = () => (modalImg.value = null)

watch(props, val => {
  if (val) {
    imgSource.value = val.image
  }
})

onMounted(() => (imgSource.value = props.image || '/static/dist/img/NoImage.jpeg'))
</script>

<template>
  <CRow class="mb-4">
    <CCol>
      <h6>프로필 이미지</h6>
      <input
        id="file"
        type="file"
        class="form-control"
        accept="image/*"
        style="display: none"
        @change="loadFile"
      />
      <CRow class="relative inline-block">
        <CCol>
          <CDropdown placement="bottom-start">
            <CDropdownToggle class="py-0 btn-link" :caret="false">
              <CImage rounded thumbnail fluid :src="imgSource" />
              <CCol
                class="bg-white text-high-emphasis position-absolute rounded-2 px-2 py-1 left-0 bottom-0 ml-1 mb-1 border"
              >
                <CIcon name="cilPencil" />
                Edit
              </CCol>
            </CDropdownToggle>
            <CDropdownMenu class="ml-2 py-1">
              <CDropdownItem @click="browse"> Upload a photo...</CDropdownItem>
            </CDropdownMenu>
          </CDropdown>
        </CCol>
      </CRow>
    </CCol>
  </CRow>

  <CropperModal
    ref="cropModal"
    :modal-img="modalImg"
    :filename="filename"
    @image-del="delModalImg"
    @trans-avatar-input="transAvatarInput"
  />
</template>

<style lang="scss" scoped>
@media (min-width: 768px) {
  .flex-md-row {
    flex-direction: row !important;
  }
}

.flex-column-reverse {
  flex-direction: column-reverse;
}

.rounded {
  border-radius: 100px !important;
  width: 200px;
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}
</style>
