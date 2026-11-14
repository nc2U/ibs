import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import {
  cleanupParams,
  errorHandle,
  getErrorData,
  getErrorMessage,
  getOrderedList,
  markdownRender,
  setLocalStorage,
} from '@/utils/helper'
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
