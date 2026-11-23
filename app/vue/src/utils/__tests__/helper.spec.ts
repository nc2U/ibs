import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import {
  cleanupParams,
  errorHandle,
  getErrorData,
  getErrorMessage,
  getOrderedList,
  markdownRender,
  sanitizeExternalUrl,
  setLocalStorage,
  stripMarkdown,
} from '@/utils/helper'
import {
  dateFormat,
  elapsedTime,
  humanizeFileSize,
  numFormat,
  parseRrnMeta,
} from '@/utils/baseMixins'
import { formatMailMergePreview } from '@/views/notices/Mailing/preview'

describe('utils/helper', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('cleanupParams strips null, undefined, and empty strings while keeping falsy 0/false', () => {
    expect(
      cleanupParams({
        page: 1,
        zero: 0,
        flag: false,
        empty: '',
        missing: undefined,
        nil: null,
        q: '검색',
      }),
    ).toEqual({ page: 1, zero: 0, flag: false, q: '검색' })
  })

  it('getOrderedList preserves saved order and appends new items', () => {
    const items = [
      { pk: 1, name: 'A' },
      { pk: 2, name: 'B' },
      { pk: 3, name: 'C' },
    ]
    setLocalStorage([items[2], items[0]], 'test-order')

    expect(getOrderedList(items, 'test-order').map(i => i.pk)).toEqual([3, 1, 2])
  })

  it('markdownRender sanitizes dangerous HTML tags and scripts', () => {
    const html = markdownRender('**안전**\n\n<script>alert(1)</script><img src=x onerror=alert(2)>')
    expect(html).toContain('<strong>안전</strong>')
    expect(html).not.toContain('<script>')
    expect(html).not.toContain('onerror')
  })

  it('stripMarkdown converts markdown and HTML into clean single-line plain text', () => {
    expect(
      stripMarkdown('### 제목입니다\n\n**굵은** [링크](https://example.com) &amp; `코드`'),
    ).toBe('제목입니다 굵은 링크 & 코드')
    expect(stripMarkdown('<script>alert(1)</script>본문')).toBe('본문')
    expect(stripMarkdown('')).toBe('')
  })

  it('getErrorData extracts response payloads safely across error shapes', () => {
    expect(getErrorData({ response: { data: { detail: '권한 없음' } } })).toEqual({
      detail: '권한 없음',
    })
    expect(getErrorData({ data: { error: '잘못된 요청' } })).toEqual({ error: '잘못된 요청' })

    const networkErr = new Error('Network Error')
    expect(getErrorData(networkErr)).toBe(networkErr)
  })

  it('getErrorMessage extracts structured API messages, Error messages, and fallbacks', () => {
    expect(getErrorMessage({ response: { data: { detail: '인증 실패' } } })).toBe('인증 실패')
    expect(
      getErrorMessage({ response: { data: { phone_number: ['유효한 전화번호가 아닙니다.'] } } }),
    ).toBe('유효한 전화번호가 아닙니다.')
    expect(getErrorMessage(new Error('Network Timeout'))).toBe('Network Timeout')
    expect(getErrorMessage(null, '기본 오류')).toBe('기본 오류')
  })

  it('errorHandle handles network errors without .response and token_not_valid safely', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    const consoleErrSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => errorHandle(new Error('Network Error'))).not.toThrow()
    expect(() => errorHandle(undefined)).not.toThrow()
    expect(() => errorHandle({ response: { data: { code: 'token_not_valid' } } })).not.toThrow()
    expect(consoleSpy).toHaveBeenCalledWith('token_not_valid')

    consoleSpy.mockRestore()
    consoleErrSpy.mockRestore()
  })

  it('sanitizeExternalUrl allows safe relative and http(s) URLs and rejects protocol-relative or dangerous schemes', () => {
    expect(sanitizeExternalUrl('/dashboard')).toBe('/dashboard')
    expect(sanitizeExternalUrl('https://example.com/path?a=1')).toBe('https://example.com/path?a=1')
    expect(sanitizeExternalUrl('//evil.com/phish')).toBe('#')
    expect(sanitizeExternalUrl('javascript:alert(1)')).toBe('#')
    expect(sanitizeExternalUrl('')).toBe('#')
  })

  it('getOrderedList falls back to original order when localStorage has malformed JSON', () => {
    const items = [
      { pk: 1, name: 'A' },
      { pk: 2, name: 'B' },
    ]
    localStorage.setItem('broken-order', '{invalid-json')
    expect(getOrderedList(items, 'broken-order').map(i => i.pk)).toEqual([1, 2])
  })
})

describe('utils/baseMixins', () => {
  it('numFormat handles valid, zero, and invalid numeric strings safely', () => {
    expect(numFormat(1234.56, 1)).toBe('1,234.6')
    expect(numFormat(0, 0, '-')).toBe('-')
    expect(numFormat(0, 0, 0)).toBe(0)
    expect(numFormat('abc')).toBe('-')
  })

  it('dateFormat and elapsedTime handle invalid dates and future timestamps gracefully', () => {
    expect(dateFormat('not-a-date')).toBe('')
    expect(dateFormat('2026-01-05', '/')).toBe('2026/01/05')
    expect(elapsedTime('not-a-date')).toBe('')
    expect(elapsedTime(Date.now() + 60_000)).toBe('방금 전')
  })

  it('humanizeFileSize handles zero, negative, and huge byte sizes without NaN or undefined units', () => {
    expect(humanizeFileSize(0)).toBe('0 Bytes')
    expect(humanizeFileSize(-100)).toBe('')
    expect(humanizeFileSize(1024)).toBe('1 KB')
    expect(humanizeFileSize(1024 ** 10)).toContain('PB')
  })

  it('parseRrnMeta extracts birthDate and gender safely for valid 13-digit RRN', () => {
    expect(parseRrnMeta('900512-1234567')).toEqual({ birthDate: '1990-05-12', gender: 'M' })
    expect(parseRrnMeta('030820-4123456')).toEqual({ birthDate: '2003-08-20', gender: 'F' })
    expect(parseRrnMeta('900230-1234567')).toBeNull()
    expect(parseRrnMeta('12345')).toBeNull()
  })
})

describe('formatMailMergePreview', () => {
  it('highlights merge tags and sanitizes XSS payloads', () => {
    const raw =
      '<p>안녕하세요 {{ name }}님</p><script>alert(1)</script><a href="javascript:alert(2)" onclick="evil()">링크</a>'
    const sanitized = formatMailMergePreview(raw)

    expect(sanitized).toContain('<span class="badge bg-primary')
    expect(sanitized).toContain('{{ name }}')
    expect(sanitized).not.toContain('<script>')
    expect(sanitized).not.toContain('onclick')
    expect(sanitized).not.toContain('javascript:')
  })

  it('returns empty string for null or empty input', () => {
    expect(formatMailMergePreview('')).toBe('')
    expect(formatMailMergePreview(null)).toBe('')
  })
})
