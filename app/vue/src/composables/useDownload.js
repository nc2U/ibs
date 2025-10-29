import { ref, reactive } from 'vue'

// 파일 타입 정의
const FILE_TYPES = {
  PDF: 'pdf',
  EXCEL: 'excel',
  WORD: 'word',
  IMAGE: 'image',
  OTHER: 'other'
}

// MIME 타입 매핑
const MIME_TYPES = {
  pdf: 'application/pdf',
  excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  xls: 'application/vnd.ms-excel',
  word: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  doc: 'application/msword',
  jpg: 'image/jpeg',
  png: 'image/png'
}

// 글로벌 다운로드 상태 관리
const downloadState = reactive({
  isDownloading: false,
  downloadUrl: null,
  fileName: null,
  fileType: null,
  progress: 0
})

export function useDownload() {
  /**
   * 파일 타입 감지
   * @param {string} fileName - 파일명
   * @returns {string} 파일 타입
   */
  const detectFileType = (fileName) => {
    const extension = fileName.split('.').pop()?.toLowerCase()

    switch (extension) {
      case 'pdf':
        return FILE_TYPES.PDF
      case 'xlsx':
      case 'xls':
      case 'csv':
        return FILE_TYPES.EXCEL
      case 'docx':
      case 'doc':
        return FILE_TYPES.WORD
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return FILE_TYPES.IMAGE
      default:
        return FILE_TYPES.OTHER
    }
  }

  /**
   * 파일 다운로드 (모든 파일 타입 지원)
   * @param {string} url - 다운로드 URL
   * @param {string} fileName - 파일명 (선택사항)
   */
  const downloadFile = async (url, fileName = 'document') => {
    try {
      // 다운로드 시작
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
      downloadState.fileType = detectFileType(fileName)
      downloadState.progress = 0

      // iframe을 사용한 다운로드 (브라우저 호환성 좋음)
      const iframe = document.createElement('iframe')
      iframe.style.display = 'none'
      iframe.src = url

      document.body.appendChild(iframe)

      // 다운로드 완료 감지 (타이머 기반)
      let progress = 0
      const progressInterval = setInterval(() => {
        progress += 10
        downloadState.progress = Math.min(progress, 90)
      }, 200)

      // 다운로드 완료 후 정리
      setTimeout(() => {
        clearInterval(progressInterval)
        downloadState.progress = 100

        setTimeout(() => {
          downloadState.isDownloading = false
          downloadState.downloadUrl = null
          downloadState.fileName = null
          downloadState.fileType = null
          downloadState.progress = 0
          document.body.removeChild(iframe)
        }, 500)
      }, 3000) // 3초 후 완료로 간주

    } catch (error) {
      console.error('다운로드 오류:', error)
      downloadState.isDownloading = false
      alert('파일 다운로드 중 오류가 발생했습니다.')
    }
  }

  /**
   * fetch를 사용한 다운로드 (실제 진행률 추적 가능)
   */
  const downloadWithProgress = async (url, fileName = 'document') => {
    try {
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
      downloadState.fileType = detectFileType(fileName)
      downloadState.progress = 0

      const response = await fetch(url)
      const reader = response.body.getReader()
      const contentLength = +response.headers.get('Content-Length')

      let receivedLength = 0
      let chunks = []

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        chunks.push(value)
        receivedLength += value.length

        // 진행률 업데이트
        downloadState.progress = Math.round((receivedLength / contentLength) * 100)
      }

      // 파일 확장자에 따른 MIME 타입 결정
      const extension = fileName.split('.').pop()?.toLowerCase()
      const mimeType = MIME_TYPES[extension] || 'application/octet-stream'

      // 파일 다운로드
      const blob = new Blob(chunks, { type: mimeType })
      const downloadUrl = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = fileName
      link.click()

      window.URL.revokeObjectURL(downloadUrl)

      // 상태 리셋
      setTimeout(() => {
        downloadState.isDownloading = false
        downloadState.downloadUrl = null
        downloadState.fileName = null
        downloadState.fileType = null
        downloadState.progress = 0
      }, 500)

    } catch (error) {
      console.error('다운로드 오류:', error)
      downloadState.isDownloading = false
      alert('파일 다운로드 중 오류가 발생했습니다.')
    }
  }

  // 호환성을 위한 기존 함수들
  const downloadPDF = (url, fileName = 'document.pdf') => downloadFile(url, fileName)
  const downloadExcel = (url, fileName = 'document.xlsx') => downloadFile(url, fileName)

  return {
    downloadState,
    downloadFile,
    downloadPDF,
    downloadExcel,
    downloadWithProgress,
    FILE_TYPES
  }
}