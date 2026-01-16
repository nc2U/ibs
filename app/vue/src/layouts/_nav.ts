const dashboard = {
  component: 'CNavItem',
  name: '대 시 보 드',
  to: '/dashboard',
  icon: 'cil-speedometer',
  badge: {
    color: 'warning',
    text: 'ing..',
  },
}

const work_project = {
  component: 'CNavItem',
  name: '업 무 관 리',
  to: '/work',
  icon: 'cil-task',
}

const work_admin = {
  component: 'CNavItem',
  name: '설 정 관 리',
  to: '/manage',
  icon: 'cil-code',
}

const company_cash = {
  component: 'CNavGroup',
  name: '본사 자금 관리',
  to: '/cashes',
  icon: 'cil-laptop',
  items: [
    {
      component: 'CNavItem',
      name: '본사 자금 현황',
      to: '/cashes/status',
    },
    {
      component: 'CNavItem',
      name: '본사 출납 내역',
      to: '/cashes/index',
    },
  ],
}

const company_ledger = {
  component: 'CNavGroup',
  name: '본사 회계 관리',
  to: '/ledger',
  icon: 'cil-laptop',
  items: [
    {
      component: 'CNavItem',
      name: '본사 정산 현황',
      to: '/ledger/status',
    },
    {
      component: 'CNavItem',
      name: '본사 거래 내역',
      to: '/ledger/index',
    },
  ],
}

const company_docs = {
  component: 'CNavGroup',
  name: '본사 문서 관리',
  to: '/docs/general',
  icon: 'cil-cloud-download',
  items: [
    {
      component: 'CNavItem',
      name: '본사 일반 문서',
      to: '/docs/general/docs',
    },
    {
      component: 'CNavItem',
      name: '본사 소송 문서',
      to: '/docs/lawsuit/docs',
    },
    {
      component: 'CNavItem',
      name: '본사 소송 사건',
      to: '/docs/lawsuit/case',
    },
    {
      component: 'CNavItem',
      name: '본사 공문 발송',
      to: '/docs/official/letters',
      badge: {
        color: 'warning',
        text: 'ing..',
      },
    },
  ],
}

const human_resource = {
  component: 'CNavGroup',
  name: '본사 인사 관리',
  to: '/hr-manage',
  icon: 'cilPeople',
  items: [
    {
      component: 'CNavItem',
      name: '직원 정보 관리',
      to: '/hr-manage/staff',
    },
    {
      component: 'CNavItem',
      name: '부서 정보 관리',
      to: '/hr-manage/department',
    },
    {
      component: 'CNavGroup',
      name: '기타 설정 관리',
      icon: 'cil-user-follow',
      items: [
        {
          component: 'CNavItem',
          name: '직위 정보 관리',
          to: '/hr-manage/position',
        },
        {
          component: 'CNavItem',
          name: '직책 정보 관리',
          to: '/hr-manage/duty',
        },
        {
          component: 'CNavItem',
          name: '직급 정보 관리',
          to: '/hr-manage/grade',
        },
      ],
    },
  ],
}

const contract = {
  component: 'CNavGroup',
  name: '공급 계약 관리',
  to: '/contracts',
  icon: 'cil-spreadsheet',
  items: [
    {
      component: 'CNavItem',
      name: '계약 내역 조회',
      to: '/contracts/index',
    },
    {
      component: 'CNavItem',
      name: '계약 상세 관리',
      to: '/contracts/detail',
    },
    {
      component: 'CNavItem',
      name: '권리 의무 승계',
      to: '/contracts/succession',
    },
    {
      component: 'CNavItem',
      name: '계약 해지 관리',
      to: '/contracts/release',
    },
    {
      component: 'CNavItem',
      name: '동호 배치 현황',
      to: '/contracts/status',
    },
  ],
}

const payments = {
  component: 'CNavGroup',
  name: '분양 수납 관리',
  to: '/payments',
  icon: 'cil-calculator',
  items: [
    {
      component: 'CNavItem',
      name: '전체 수납 내역',
      to: '/payments/index',
    },
    {
      component: 'CNavItem',
      name: '건별 수납 관리',
      to: '/payments/manage',
    },
    {
      component: 'CNavItem',
      name: '수납 현황 집계',
      to: '/payments/status',
    },
  ],
}

const payment = {
  component: 'CNavGroup',
  name: '계약 납부 관리',
  to: '/payment',
  icon: 'cil-calculator',
  badge: {
    color: 'info',
    text: 'new..',
  },
  items: [
    {
      component: 'CNavItem',
      name: '전체 납부 내역',
      to: '/payment/index',
    },
    {
      component: 'CNavItem',
      name: '건별 납부 관리',
      to: '/payment/manage',
    },
    {
      component: 'CNavItem',
      name: '납부 현황 집계',
      to: '/payment/status',
    },
  ],
}

const notice = {
  component: 'CNavGroup',
  name: '고객 고지 관리',
  to: '/notices',
  icon: 'cil-envelope-letter',
  items: [
    {
      component: 'CNavItem',
      name: '수납 고지서 출력',
      to: '/notices/bill',
    },
    {
      component: 'CNavItem',
      name: 'SMS 발송 관리',
      to: '/notices/sms',
    },
    // {
    //   component: 'CNavItem',
    //   name: 'MAIL 발송 관리',
    //   to: '/notices/mailing',
    //   badge: {
    //     color: 'danger',
    //     text: 'u.c',
    //   },
    // },
    // {
    //   component: 'CNavItem',
    //   name: '우편 라벨 관리',
    //   to: '/notices/post-label',
    //   badge: {
    //     color: 'danger',
    //     text: 'u.c',
    //   },
    // },
    // {
    //   component: 'CNavItem',
    //   name: '발송 기록 관리',
    //   to: '/notices/log',
    //   badge: {
    //     color: 'danger',
    //     text: 'u.c',
    //   },
    // },
  ],
}

const project_cash = {
  component: 'CNavGroup',
  name: 'PR 자금 관리',
  to: '/project-cash',
  icon: 'cil-money',
  items: [
    {
      component: 'CNavItem',
      name: 'PR 자금 현황',
      to: '/project-cash/status',
    },
    {
      component: 'CNavItem',
      name: 'PR 출납 내역',
      to: '/project-cash/index',
    },
    {
      component: 'CNavItem',
      name: '운영 비용 내역',
      to: '/project-cash/imprest',
    },
  ],
}

const project_ledger = {
  component: 'CNavGroup',
  name: 'PR 회계 관리',
  to: '/project-ledger',
  icon: 'cil-money',
  badge: {
    color: 'info',
    text: 'new..',
  },
  items: [
    {
      component: 'CNavItem',
      name: 'PR 정산 현황',
      to: '/project-ledger/status',
    },
    {
      component: 'CNavItem',
      name: 'PR 거래 내역',
      to: '/project-ledger/index',
    },
    {
      component: 'CNavItem',
      name: '운영 계좌 내역',
      to: '/project-ledger/imprest',
    },
  ],
}

const project_docs = {
  component: 'CNavGroup',
  name: 'PR 문서 관리',
  to: '/project-docs',
  icon: 'cil-library',
  items: [
    {
      component: 'CNavItem',
      name: 'PR 일반 문서',
      to: '/project-docs/general/docs',
    },
    {
      component: 'CNavItem',
      name: 'PR 소송 문서',
      to: '/project-docs/lawsuit/docs',
    },
    {
      component: 'CNavItem',
      name: 'PR 소송 사건',
      to: '/project-docs/lawsuit/case',
    },
  ],
}

const project = {
  component: 'CNavGroup',
  name: 'PR 등록 관리',
  to: '/project',
  icon: 'cil-building',
  items: [
    {
      component: 'CNavItem',
      name: '신규 PR 등록',
      to: '/project/manage/index',
    },
    {
      component: 'CNavGroup',
      name: '차수 타입 관리',
      icon: 'cil-list-numbered',
      items: [
        {
          component: 'CNavItem',
          name: '차수 분류 등록',
          to: '/project/manage/order',
        },
        {
          component: 'CNavItem',
          name: '타입 정보 등록',
          to: '/project/manage/type',
        },
        {
          component: 'CNavItem',
          name: '층별 조건 등록',
          to: '/project/settings/floor',
        },
      ],
    },
    {
      component: 'CNavGroup',
      name: '유닛 등록 관리',
      icon: 'cil-room',
      items: [
        {
          component: 'CNavItem',
          name: '동(건물) 등록',
          to: '/project/settings/bldg',
        },
        {
          component: 'CNavItem',
          name: '호(유닛) 등록',
          to: '/project/settings/unit',
        },
      ],
    },
    {
      component: 'CNavGroup',
      name: '예산 등록 관리',
      icon: 'cil-exposure',
      items: [
        {
          component: 'CNavItem',
          name: '수입 예산 등록',
          to: '/project/manage/inc-budget',
        },
        {
          component: 'CNavItem',
          name: '지출 예산 등록',
          to: '/project/manage/out-budget',
        },
      ],
    },
    {
      component: 'CNavGroup',
      name: '분양 계약 조건',
      icon: 'cil-cog',
      items: [
        {
          component: 'CNavItem',
          name: '납부 회차 등록',
          to: '/project/settings/payment-order',
        },
        {
          component: 'CNavItem',
          name: '계약 금액 등록',
          to: '/project/settings/down-payment',
        },
        {
          component: 'CNavItem',
          name: '공급 가격 등록',
          to: '/project/settings/price',
        },
        {
          component: 'CNavItem',
          name: '구비 서류 등록',
          to: '/project/settings/required',
        },
        {
          component: 'CNavItem',
          name: '옵션 품목 등록',
          to: '/project/settings/options',
        },
      ],
    },
    {
      component: 'CNavGroup',
      name: '사업 부지 관리',
      icon: 'cil-location-pin',
      items: [
        {
          component: 'CNavItem',
          name: '지번 목록 관리',
          to: '/project/site/index',
        },
        {
          component: 'CNavItem',
          name: '소유자 별 관리',
          to: '/project/site/owner',
        },
        {
          component: 'CNavItem',
          name: '매입 계약 관리',
          to: '/project/site/contract',
        },
      ],
    },
  ],
}

const settings = {
  component: 'CNavGroup',
  name: '환 경 설 정',
  to: '/settings',
  icon: 'cil-settings',
  items: [
    {
      component: 'CNavItem',
      name: '회사 정보 관리',
      to: '/settings/company',
    },
    {
      component: 'CNavItem',
      name: '권한 설정 관리',
      to: '/settings/authorization',
    },
  ],
}

const nav = [
  dashboard,
  work_project,
  work_admin,
  {
    component: 'CNavTitle',
    name: '본사 관리',
  },
  // company_cash,
  company_ledger,
  company_docs,
  human_resource,
  {
    component: 'CNavTitle',
    name: '프로젝트 관리',
  },
  contract,
  // payments,
  payment,
  notice,
  project_cash,
  project_ledger,
  project_docs,
  project,
  {
    component: 'CNavTitle',
    name: '기타 관리',
  },
  settings,
]

export default nav
