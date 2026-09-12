<script setup lang="ts">
import { computed } from 'vue'
import { markdownRender } from '@/utils/helper.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type { Company, CompanySeal } from '@/store/types/settings'
import type { OfficialLetter } from '@/store/types/docs'
import type { LocalAttachmentItem } from './LetterForm.vue'

defineProps<{
  form: OfficialLetter
  currentCompany?: Company | null
  selectedSeal?: CompanySeal | null
  selectedSealImage?: string | null
  selectedCoSeal?: CompanySeal | null
  selectedCoSealImage?: string | null
  representativesList: Array<{ title: string; name: string }>
  representativeName: string
  approverDutyTitle: string
  finalApproverName: string
  approvalMode: 'approval' | 'manual'
  isSoloApproval: boolean
  senderContact: { phone: string; fax: string; email: string }
  cleanDrafterName: string
  nextDocNumber: string
  attachmentInputMode: 'file' | 'text'
  pendingAttachments: LocalAttachmentItem[]
}>()

const accStore = useAccount()
</script>

<template>
  <div class="sticky-top" style="top: 20px; z-index: 10">
    <div class="d-flex justify-content-between align-items-center mb-2">
      <span class="fw-bold text-secondary">
        <v-icon icon="mdi-printer-outline" class="me-1" />
        실시간 인쇄 미리보기 (A4 Live Preview)
      </span>
      <CBadge color="info">실시간 반영중</CBadge>
    </div>

    <!-- A4 종이 프리뷰 컨테이너 (A4 비율 210:297 고정) -->
    <div class="a4-preview-wrapper d-flex justify-content-center">
      <div class="a4-preview-sheet shadow border bg-white p-4">
        <!-- 1. 레터헤드 -->
        <div class="preview-letterhead text-center pb-2 mb-2 border-bottom position-relative">
          <div class="preview-company-name fw-bold" style="font-size: 1.15rem; letter-spacing: 2px">
            {{ currentCompany?.name || '회사명' }}
          </div>
          <div class="text-muted" style="font-size: 0.72rem; line-height: 1.3">
            <span v-if="currentCompany?.ceo">대표이사 {{ currentCompany.ceo }} | </span>
            <span v-if="currentCompany?.tax_number">
              사업자등록번호 {{ currentCompany.tax_number }}
            </span>
            <br />
            <span>
              <span v-if="currentCompany?.zipcode">[{{ currentCompany.zipcode }}]</span>
              {{ currentCompany?.address1 }} {{ currentCompany?.address2 || '' }}
              {{ currentCompany?.address3 || '' }}
            </span>
          </div>
          <!-- 영문 그라데이션 띠 -->
          <div
            class="preview-en-bar text-center text-white mt-1"
            style="
              height: 8px;
              line-height: 8px;
              font-size: 6px;
              background: linear-gradient(to right, #666 0%, #777 30%, #999 70%, #aaa 100%);
            "
          >
            {{ currentCompany?.en_name || '' }}
          </div>
        </div>

        <!-- 2. 수신처 정보 (4행 고정) -->
        <div class="preview-recipient mb-2">
          <table class="w-100" style="font-size: 0.8rem; line-height: 1.5">
            <tbody>
              <tr>
                <td style="width: 55px; font-weight: bold; color: #555">수 신</td>
                <td>{{ form.recipient_name || '(수신처 미입력)' }}</td>
              </tr>
              <tr>
                <td style="font-weight: bold; color: #555">경 유</td>
                <td>{{ form.via || '' }}</td>
              </tr>
              <tr>
                <td style="font-weight: bold; color: #555">참 조</td>
                <td>{{ form.recipient_reference || '' }}</td>
              </tr>
              <tr class="fw-bold" style="border-bottom: 2px solid #333">
                <td style="color: #111; padding-bottom: 4px">제 목</td>
                <td style="padding-bottom: 4px">{{ form.title || '(제목 미입력)' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 3. 본문 영역 (가변 확장 및 내용 스크롤 지원) -->
        <div
          class="preview-content my-2 p-3"
          style="
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            font-size: 0.82rem;
            line-height: 1.7;
            word-break: break-all;
            text-align: justify;
          "
        >
          <div
            v-if="form.content"
            class="preview-markdown-body"
            v-html="markdownRender(form.content)"
          />
          <div v-else class="text-muted">
            공문 본문 내용이 여기에 실시간으로 표시됩니다.
          </div>

          <!-- 붙임 목록 -->
          <div v-if="attachmentInputMode === 'file'" class="mt-3 pt-2">
            <div
              v-if="
                (form.attachments && form.attachments.length > 0) ||
                pendingAttachments.length > 0
              "
            >
              <div class="fw-bold mb-1" style="font-size: 0.78rem">붙임:</div>
              <div
                v-for="(att, idx) in form.attachments"
                :key="'ex-' + idx"
                style="font-size: 0.78rem; padding-left: 10px"
              >
                {{ idx + 1 }}. {{ att.name || att.file_name }} {{ att.quantity || '1부' }}.
              </div>
              <div
                v-for="(att, idx) in pendingAttachments"
                :key="'new-' + idx"
                style="font-size: 0.78rem; padding-left: 10px"
              >
                {{ (form.attachments?.length || 0) + idx + 1 }}.
                {{ att.name || att.file.name }} {{ att.quantity || '1부' }}.
              </div>
            </div>
          </div>
          <div v-else-if="form.attachment_text" class="mt-3 pt-2">
            <div class="fw-bold mb-1" style="font-size: 0.78rem">붙임:</div>
            <div style="font-size: 0.78rem; padding-left: 10px; white-space: pre-wrap">
              {{ form.attachment_text }}
            </div>
          </div>
        </div>

        <!-- 4 & 5. 바닥 영역 (서명 + 메타정보) -->
        <div class="preview-bottom-wrapper mt-auto">
          <!-- 4. 하단 서명 / 직인 날인 -->
          <div class="preview-signature text-center my-2">
            <!-- 공동대표 병기 모드 (가로 나란히 나열) -->
            <template v-if="form.sender_display_type === 'co_rep'">
              <div class="fw-bold mb-1" style="font-size: 1.05rem">
                {{ currentCompany?.name || '회사명' }}
              </div>
              <div class="d-inline-flex align-items-center justify-content-center gap-4">
                <!-- 공동대표 1 -->
                <div
                  class="fw-bold d-inline-flex align-items-center"
                  style="font-size: 0.95rem"
                >
                  <span
                    >{{ representativesList[0]?.title || '공동대표이사' }}
                    {{ representativesList[0]?.name || finalApproverName }}</span
                  >
                  <span v-if="selectedSealImage" class="ms-2">
                    <img
                      :src="selectedSealImage"
                      alt="인장1"
                      style="width: 32px; height: 32px; object-fit: contain"
                    />
                  </span>
                  <span
                    v-else
                    class="ms-2 text-muted border border-secondary rounded-circle d-inline-flex align-items-center justify-content-center"
                    style="width: 26px; height: 26px; font-size: 0.7rem"
                  >
                    (인)
                  </span>
                </div>
                <!-- 공동대표 2 -->
                <div
                  class="fw-bold d-inline-flex align-items-center"
                  style="font-size: 0.95rem"
                >
                  <span
                    >{{ representativesList[1]?.title || '공동대표이사' }}
                    {{ representativesList[1]?.name || '대표2' }}</span
                  >
                  <span v-if="selectedCoSealImage" class="ms-2">
                    <img
                      :src="selectedCoSealImage"
                      alt="인장2"
                      style="width: 32px; height: 32px; object-fit: contain"
                    />
                  </span>
                  <span
                    v-else
                    class="ms-2 text-muted border border-secondary rounded-circle d-inline-flex align-items-center justify-content-center"
                    style="width: 26px; height: 26px; font-size: 0.7rem"
                  >
                    (인)
                  </span>
                </div>
              </div>
            </template>

            <!-- 회사명 + 대표직함·성명 표기 모드 -->
            <template v-else-if="form.sender_display_type === 'company_rep'">
              <div class="fw-bold d-inline-flex align-items-center" style="font-size: 1.05rem">
                <span>{{ currentCompany?.name || '회사명' }}</span>
                <span class="ms-3">{{ approverDutyTitle }} {{ finalApproverName }}</span>
                <span v-if="selectedSealImage" class="ms-2">
                  <img
                    :src="selectedSealImage"
                    alt="직인"
                    style="width: 36px; height: 36px; object-fit: contain"
                  />
                </span>
                <span
                  v-else
                  class="ms-2 text-muted border border-secondary rounded-circle d-inline-flex align-items-center justify-content-center"
                  style="width: 30px; height: 30px; font-size: 0.75rem"
                >
                  (인)
                </span>
              </div>
            </template>

            <!-- 기본형: 회사명만 표기 모드 -->
            <template v-else>
              <div class="fw-bold d-inline-flex align-items-center" style="font-size: 1.05rem">
                <span>{{ currentCompany?.name || '회사명' }}</span>
                <span v-if="selectedSealImage" class="ms-2">
                  <img
                    :src="selectedSealImage"
                    alt="직인"
                    style="width: 36px; height: 36px; object-fit: contain"
                  />
                </span>
                <span
                  v-else
                  class="ms-2 text-muted border border-secondary rounded-circle d-inline-flex align-items-center justify-content-center"
                  style="width: 30px; height: 30px; font-size: 0.75rem"
                >
                  (인)
                </span>
              </div>
            </template>
          </div>

          <!-- 5. 결재선 및 시행 메타 -->
          <div
            class="preview-bottom pt-2"
            style="font-size: 0.72rem; line-height: 1.4; border-top: 2px solid #333333"
          >
            <table
              class="w-100"
              style="color: #444; border-collapse: collapse; font-size: 0.72rem"
            >
              <tbody>
                <!-- 1행: 결재선 -->
                <tr class="border-bottom">
                  <td
                    class="pb-1"
                    style="width: 40px; vertical-align: bottom; padding-left: 0"
                  >
                    <template v-if="!isSoloApproval">
                      <span class="text-secondary">담당</span>
                    </template>
                  </td>
                  <td colspan="2" class="pb-1" style="vertical-align: bottom">
                    <template v-if="!isSoloApproval">
                      <span class="fw-bold text-dark">{{
                        approvalMode === 'approval'
                          ? accStore.userInfo?.staff_name ||
                            accStore.userInfo?.profile?.name ||
                            accStore.userInfo?.username ||
                            '기안자'
                          : cleanDrafterName || form.drafter_name || '담당자'
                      }}</span>
                    </template>
                    <span v-else class="text-muted fst-italic"
                      >({{ approverDutyTitle }} 직접 기안)</span
                    >
                  </td>
                  <td colspan="2" class="text-end pb-1" style="vertical-align: bottom">
                    <div class="text-muted" style="font-size: 0.65rem; margin-bottom: 1px">
                      <span v-if="approvalMode === 'approval'" class="badge bg-secondary">
                        결재 승인 시 자동 확정
                      </span>
                      <span v-else>
                        {{
                          ['현장소장', '소장', '본부장', '팀장'].includes(approverDutyTitle)
                            ? '전결'
                            : '시행'
                        }}
                        {{ form.issue_date || '발신일자' }}
                      </span>
                    </div>
                    <div>
                      <span class="me-1 text-secondary">
                        {{ approverDutyTitle }}
                      </span>
                      <span class="fw-bold text-dark">{{ finalApproverName }}</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td
                    style="
                      width: 40px;
                      font-weight: bold;
                      padding-left: 0;
                      padding-top: 4px;
                    "
                  >
                    시행
                  </td>
                  <td style="width: 140px; padding-top: 4px">
                    {{ form.document_number || nextDocNumber || '자동채번' }}
                  </td>
                  <td style="width: 110px; padding-top: 4px">
                    ({{
                      approvalMode === 'approval'
                        ? form.effective_issue_date || form.issue_date || '승인일 확정'
                        : form.effective_issue_date || form.issue_date || '발신일자'
                    }})
                  </td>
                  <td style="width: 40px; font-weight: bold; padding-top: 4px">접수</td>
                  <td style="padding-top: 4px"></td>
                </tr>
                <tr>
                  <td style="font-weight: bold">우편</td>
                  <td colspan="4">
                    <span v-if="form.sender_address">
                      <span v-if="form.sender_zipcode">({{ form.sender_zipcode }}) </span>
                      {{ form.sender_address }}
                    </span>
                    <span v-else>
                      <span v-if="currentCompany?.zipcode"
                        >({{ currentCompany.zipcode }})
                      </span>
                      {{ currentCompany?.address1 }} {{ currentCompany?.address2 || '' }}
                      {{ currentCompany?.address3 || '' }}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style="font-weight: bold">전화</td>
                  <td style="width: 130px">{{ senderContact.phone }}</td>
                  <td style="width: 35px; font-weight: bold">팩스</td>
                  <td style="width: 120px">{{ senderContact.fax }}</td>
                  <td>
                    <div class="d-flex justify-content-between align-items-center">
                      <span>{{ senderContact.email }}</span>
                      <span class="text-end text-dark fw-normal ps-1">
                        <span class="text-secondary me-1">/</span>
                        <span class="fw-semibold">
                          {{
                            form.disclosure_type === '2'
                              ? '부분공개'
                              : form.disclosure_type === '3'
                                ? '비공개'
                                : '공개'
                          }}
                        </span>
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.a4-preview-wrapper {
  width: 100%;
}

.a4-preview-sheet {
  width: 100%;
  max-width: 100%;
  max-height: calc(100vh - 110px);
  aspect-ratio: 210 / 297;
  display: flex;
  flex-direction: column;
  background-color: #ffffff !important;
  color: #111111 !important;
  font-family: 'Nanum Gothic', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  border: 1px solid #ced4da;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

.preview-content {
  background-color: transparent !important;
  color: #111111 !important;
}

:deep(.preview-markdown-body) {
  width: 100%;
  color: #111111 !important;
}

:deep(.preview-markdown-body *) {
  color: inherit;
}

:deep(.preview-markdown-body p) {
  margin-bottom: 0.5rem;
}

:deep(.preview-markdown-body ol),
:deep(.preview-markdown-body ul) {
  padding-left: 1.25rem;
  margin: 0.4rem 0 0.6rem 0;
}

:deep(.preview-markdown-body li) {
  margin-bottom: 0.35rem;
  line-height: 1.7;
}

:deep(.preview-markdown-body li > p) {
  margin-bottom: 0.25rem;
}

:deep(.preview-markdown-body blockquote) {
  border-left: 3px solid #888;
  padding-left: 10px;
  margin: 0.5rem 0;
  color: #555;
}

:deep(.preview-markdown-body p.empty-line) {
  margin-bottom: 0.5rem;
  line-height: 1.7;
}

:deep(.preview-markdown-body table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0;
  font-size: 0.75rem;
  background-color: #ffffff;
  white-space: normal;
}

:deep(.preview-markdown-body th),
:deep(.preview-markdown-body td) {
  border: 1px solid #ced4da;
  padding: 3px 6px;
  text-align: center;
  color: #111111 !important;
}

:deep(.preview-markdown-body th) {
  background-color: #f8f9fa !important;
  color: #111111 !important;
}

:deep(.preview-markdown-body center) {
  display: block;
  text-align: center;
  margin: 0.5rem 0;
}
</style>
