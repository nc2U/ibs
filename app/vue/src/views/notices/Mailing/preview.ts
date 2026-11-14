import DOMPurify from 'dompurify'

/**
 * 이메일 본문 내 `{{ 변수 }}` 머지 태그를 코드 뱃지로 강조하고 XSS 방지를 위해 HTML 을 Sanitize 합니다.
 */
export function formatMailMergePreview(content: string | null | undefined): string {
  if (!content) return ''
  const replaced = content.replace(
    /(\{\{\s*[^}]+\s*\}\})/g,
    '<span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-1 py-0 rounded font-monospace">$1</span>',
  )
  return DOMPurify.sanitize(replaced)
}
