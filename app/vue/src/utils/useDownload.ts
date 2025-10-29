import { reactive } from 'vue'

// 파일 타입 정의
export const FILE_TYPES = {
  PDF: 'pdf',
  EXCEL: 'excel',
  WORD: 'word',
  IMAGE: 'image',
  OTHER: 'other',
} as const

export type FileType = (typeof FILE_TYPES)[keyof typeof FILE_TYPES]

// MIME 타입 매핑
const MIME_TYPES: Record<string, string> = {
  pdf: 'application/pdf',
  excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  xls: 'application/vnd.ms-excel',
  word: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  doc: 'application/msword',
  jpg: 'image/jpeg',
  png: 'image/png',
}

// 다운로드 상태 타입
export interface DownloadState {
  isDownloading: boolean
  downloadUrl: string | null
  fileName: string | null
  fileType: FileType | null
  progress: number
}

// 글로벌 다운로드 상태 관리
const downloadState = reactive<DownloadState>({
  isDownloading: false,
  downloadUrl: null,
  fileName: null,
  fileType: null,
  progress: 0,
})

// useDownload 훅 반환 타입
export interface UseDownloadReturn {
  downloadState: DownloadState
  downloadFile: (url: string, fileName?: string) => Promise<void>
  downloadPDF: (url: string, fileName?: string) => Promise<void>
  downloadExcel: (url: string, fileName?: string) => Promise<void>
  downloadWithProgress: (url: string, fileName?: string) => Promise<void>
  FILE_TYPES: typeof FILE_TYPES
}

export function useDownload(): UseDownloadReturn {
  /**
   * 파일 타입 감지
   * @param fileName - 파일명
   * @returns 파일 타입
   */
  const detectFileType = (fileName: string): FileType => {
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
   * @param url - 다운로드 URL
   * @param fileName - 파일명 (선택사항)
   */
  const downloadFile = async (url: string, fileName: string = 'document'): Promise<void> => {
    try {
      // 다운로드 시작
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
      downloadState.fileType = detectFileType(fileName)
      downloadState.progress = 0

      // URL에 filename 파라미터 추가
      let finalUrl = url
      if (fileName && fileName !== 'document') {
        const separator = url.includes('?') ? '&' : '?'
        // 확장자 제거하여 서버에서 확장자를 추가하도록 함
        const nameWithoutExt = fileName.replace(/\.(pdf|xlsx?|docx?|png|jpe?g|gif)$/i, '')
        finalUrl = `${url}${separator}filename=${encodeURIComponent(nameWithoutExt)}`
      }

      // 진행률 시뮬레이션
      let progress = 0
      const progressInterval = setInterval(() => {
        progress += 25
        downloadState.progress = Math.min(progress, 90)
      }, 200)

      try {
        // fetch API를 사용하여 서버의 Content-Disposition 헤더를 존중
        const response = await fetch(finalUrl, {
          method: 'GET',
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        // Content-Disposition 헤더에서 파일명 추출
        const disposition = response.headers.get('Content-Disposition')
        let downloadFileName = fileName

        if (disposition) {
          // RFC 5987 형식 (filename*=UTF-8''encoded-name) 우선 처리
          const filenameStarMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
          if (filenameStarMatch) {
            downloadFileName = decodeURIComponent(filenameStarMatch[1])
          } else {
            // 일반 filename 형식 처리
            const filenameMatch = disposition.match(/filename="?([^";]+)"?/i)
            if (filenameMatch) {
              downloadFileName = filenameMatch[1]
            }
          }
        }

        // Blob으로 변환하여 다운로드
        const blob = await response.blob()
        const blobUrl = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = blobUrl
        a.download = downloadFileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(blobUrl)
      } catch (fetchError) {
        console.warn('Fetch download failed, falling back to window.location.href', fetchError)
        // 실패 시 기존 방식으로 fallback
        window.location.href = finalUrl
      }

      // 다운로드 완료 후 정리
      clearInterval(progressInterval)
      downloadState.progress = 100

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

  /**
   * fetch를 사용한 다운로드 (실제 진행률 추적 가능)
   * @param url - 다운로드 URL
   * @param fileName - 파일명 (선택사항)
   */
  const downloadWithProgress = async (
    url: string,
    fileName: string = 'document',
  ): Promise<void> => {
    try {
      downloadState.isDownloading = true
      downloadState.downloadUrl = url
      downloadState.fileName = fileName
      downloadState.fileType = detectFileType(fileName)
      downloadState.progress = 0

      const response = await fetch(url)

      if (!response.body) {
        throw new Error('Response body is null')
      }

      const reader = response.body.getReader()
      const contentLength = +(response.headers.get('Content-Length') ?? '0')

      let receivedLength = 0
      const chunks: Uint8Array[] = []

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        if (value) {
          chunks.push(value)
          receivedLength += value.length

          // 진행률 업데이트
          if (contentLength > 0) {
            downloadState.progress = Math.round((receivedLength / contentLength) * 100)
          }
        }
      }

      // 파일 확장자에 따른 MIME 타입 결정
      const extension = fileName.split('.').pop()?.toLowerCase()
      const mimeType = (extension && MIME_TYPES[extension]) || 'application/octet-stream'

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
  const downloadPDF = async (url: string, fileName: string = 'document.pdf'): Promise<void> => {
    return downloadFile(url, fileName)
  }

  const downloadExcel = async (url: string, fileName: string = 'document.xlsx'): Promise<void> => {
    return downloadFile(url, fileName)
  }

  return {
    downloadState,
    downloadFile,
    downloadPDF,
    downloadExcel,
    downloadWithProgress,
    FILE_TYPES,
  }
}
