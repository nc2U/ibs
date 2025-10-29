import { ref, reactive } from 'vue'

// 글로벌 다운로드 상태 관리
const downloadState = reactive({
  isDownloading: false,
  downloadUrl: null,
  fileName: null,
  progress: 0
})

export function useDownload() {
  /**
   * PDF 파일 다운로드 (로딩 인디케이터 포함)
   * @param {string} url - 다운로드 URL
   * @param {string} fileName - 파일명 (선택사항)
   */
  const downloadPDF = async (url, fileName = 'document.pdf') => {
    try {
      // 다운로드 시작
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
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
  const downloadWithProgress = async (url, fileName = 'document.pdf') => {
    try {
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
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

      // 파일 다운로드
      const blob = new Blob(chunks, { type: 'application/pdf' })
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
        downloadState.progress = 0
      }, 500)

    } catch (error) {
      console.error('다운로드 오류:', error)
      downloadState.isDownloading = false
      alert('파일 다운로드 중 오류가 발생했습니다.')
    }
  }

  return {
    downloadState,
    downloadPDF,
    downloadWithProgress
  }
}