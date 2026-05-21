import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'ko-KR',
  title: 'IBS',
  titleTemplate: 'IBS - Intelligent Build System',
  description: '부동산 개발관리 프로그램 매뉴얼',
  base: process.env.NODE_ENV === 'production' ? '/ibs/' : '',
  head: [
    [
      'link',
      {
        rel: 'shortcut icon',
        href: 'https://github.com/nc2U/ibs/blob/master/app/vue/docs/favicon.png?raw=true',
      },
    ],
  ],
  lastUpdated: true,
  markdown: {
    theme: 'material-theme-palenight',
    // theme: 'Shiki.IThemeRegistration',
    // lineNumbers: true,
  },
  themeConfig: {
    logo: 'https://raw.githubusercontent.com/nc2U/ibs/a39d44a6f22b37ce7444a5102fa7bb4d9b00db66/app/vue/docs/favicon.svg',
    siteTitle: 'DAEYOUNG IBS',
    nav: [
      { text: '가이드', link: '/intro/getting-started' },
      {
        text: '관련 사이트',
        items: [
          { text: 'IBS', link: 'https://ibs.dyibs.com' },
          { text: '관리자 페이지', link: 'https://ibs.dyibs.com/admin/' },
        ],
      },
    ],
    sidebar: [
      {
        text: '소개',
        items: [
          { text: 'IBS란?', link: '/' },
          { text: '시작하기', link: '/intro/getting-started' },
        ],
      },
      {
        text: '프로젝트 관리',
        items: [
          { text: '프로젝트 등록', link: '/project/' },
          { text: '차수 타입 설정', link: '/project/types' },
          { text: '유닛 정보 설정', link: '/project/units' },
          { text: '예산 정보 설정', link: '/project/budgets' },
          { text: '분양 조건 설정', link: '/project/settings' },
          { text: '부지 정보 관리', link: '/project/site-manage' },
        ],
      },
      {
        text: '계약 정보 관리',
        items: [
          { text: '계약 등록 조회', link: '/contract/' },
          { text: '계약 상세 관리', link: '/contract/details' },
          { text: '권리 의무 승계', link: '/contract/succession' },
          { text: '계약 해지 관리', link: '/contract/release' },
          { text: '동호 배치 현황', link: '/contract/status' },
        ],
      },
      {
        text: '계약 납부 관리',
        items: [
          { text: '납부 내역 관리', link: '/payment/' },
          { text: '건별 납부 관리', link: '/payment/manage' },
          { text: '납부 현황 집계', link: '/payment/status' },
        ],
      },
      {
        text: '고객 고지 관리',
        items: [
          { text: '수납 고지서 출력', link: '/notice/bill' },
          { text: 'SMS 발송 관리', link: '/notice/sms' },
        ],
      },
      {
        text: '회계 자금 관리',
        items: [
          { text: '정산 현황 관리', link: '/ledger/status' },
          { text: '거래 내역 관리', link: '/ledger/manage' },
          { text: '운영비 내역 관리', link: '/ledger/imprest' },
        ],
      },
      {
        text: '문서 소송 관리',
        items: [
          { text: '일반 문서 관리', link: '/document/' },
          { text: '소송 문서 관리', link: '/document/legal-docs' },
          { text: '소송 사건 관리', link: '/document/legal-case' },
        ],
      },
      {
        text: '권한 관리',
        items: [
          { text: '사용자 권한', link: '/authority/' },
          { text: '관리자 페이지', link: '/authority/admin-page' },
        ],
      },
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/nc2U/ibs' },
      { icon: 'slack', link: 'https://br-on.slack.com' },
    ],
    editLink: {
      pattern: 'https://github.com/nc2U/ibs/blob/master/app/vue/docs/:path',
      text: 'Edit this page on GitHub',
    },
    carbonAds: {
      code: 'your-carbon-code',
      placement: 'your-carbon-placement',
    },
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2020-present IBS',
    },
  },
})
