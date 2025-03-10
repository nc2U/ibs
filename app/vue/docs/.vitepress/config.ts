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
    logo: 'https://raw.githubusercontent.com/nc2U/ibs/5cb17e51c3cf430d2d54c10dc512425d170976d4/app/vue/docs/favicon.svg',
    siteTitle: 'IBS',
    nav: [
      { text: '가이드', link: '/intro/getting-started' },
      {
        text: '관련 사이트',
        items: [
          { text: 'IBS', link: 'https://dyibs.com' },
          { text: '관리자 페이지', link: 'https://dyibs.com/admin/' },
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
        text: '기본 설정',
        items: [
          { text: '회사정보 설정', link: '/settings/company' },
          { text: '프로젝트 설정', link: '/settings/project' },
          { text: '세부정보 설정', link: '/settings/details' },
          { text: '부지정보 관리', link: '/settings/site-manage' },
        ],
      },
      {
        text: '계약 수납 관리',
        items: [
          { text: '계약 관리', link: '/contract/' },
          { text: '수납 관리', link: '/contract/payment' },
          { text: '고지서 관리', link: '/contract/bill-notice' },
        ],
      },
      {
        text: '일반 입출금 관리',
        items: [
          { text: '기본 설정', link: '/cashes/settings' },
          { text: '입출금 관리', link: '/cashes/manage' },
        ],
      },
      {
        text: '문서 관리',
        items: [
          { text: '일반 문서', link: '/document/' },
          { text: '소송 기록', link: '/document/legal-case' },
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
