import 'package:flutter/material.dart';
import '../../auth/services/auth_service.dart';
import '../../auth/views/login_page.dart';

class MainPage extends StatefulWidget {
  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _selectedIndex = 0;
  final AuthService _authService = AuthService();

  // 선택된 프로젝트
  String _selectedProject = '반포 아크로리버파크 신축공사';
  final List<Map<String, String>> _projectList = [
    {'name': '반포 아크로리버파크 신축공사', 'code': 'P-2026-01', 'status': '진행중 🟢'},
    {'name': '성수 지식산업센터 건립공사', 'code': 'P-2026-02', 'status': '진행중 🟢'},
    {'name': '해운대 오피스텔 분양사업', 'code': 'P-2025-09', 'status': '준공준비 🟡'},
  ];

  Future<void> _handleLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('로그아웃', style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('IBS워크스페이스에서 로그아웃 하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red[600],
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await _authService.logout();
      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginPage()),
      );
    }
  }

  // 모던 Bottom Sheet 형태의 현장 선택 팝업
  void _showProjectBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  '현장(프로젝트) 선택',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
                const SizedBox(height: 12),
                ..._projectList.map((project) {
                  final isSelected = project['name'] == _selectedProject;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? const Color(0xFFEFF6FF) : Colors.grey[50],
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected ? const Color(0xFF2563EB) : Colors.grey[200]!,
                        width: isSelected ? 1.5 : 1,
                      ),
                    ),
                    child: ListTile(
                      title: Text(
                        project['name']!,
                        style: TextStyle(
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? const Color(0xFF1E40AF) : Colors.black87,
                        ),
                      ),
                      subtitle: Text('${project['code']} | ${project['status']}'),
                      trailing: isSelected
                          ? const Icon(Icons.check_circle_rounded, color: Color(0xFF2563EB))
                          : null,
                      onTap: () {
                        setState(() {
                          _selectedProject = project['name']!;
                        });
                        Navigator.pop(context);
                      },
                    ),
                  );
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A), // Premium Deep Slate Navy
        foregroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: [
            Image.asset(
              'assets/images/logo.png',
              width: 30,
              height: 30,
            ),
            const SizedBox(width: 10),
            const Text(
              'IBS워크스페이스',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold, letterSpacing: -0.5),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, size: 24),
            tooltip: '알림',
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, size: 22),
            tooltip: '로그아웃',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: const Color(0xFF2563EB),
        unselectedItemColor: const Color(0xFF64748B),
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        unselectedLabelStyle: const TextStyle(fontSize: 12),
        elevation: 8,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.grid_view_rounded),
            label: '홈',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.assignment_rounded),
            label: '업무관리',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.business_center_rounded),
            label: '프로젝트',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.drive_file_move_rounded),
            label: '공용문서',
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    switch (_selectedIndex) {
      case 0:
        return _buildHomeTab();
      case 1:
        return const Center(child: Text('업무 관리 (Issue / Meeting)'));
      case 2:
        return const Center(child: Text('프로젝트 관리 (Contract / Ledger)'));
      case 3:
        return const Center(child: Text('공용 문서 섹션 (Docs)'));
      default:
        return _buildHomeTab();
    }
  }

  Widget _buildHomeTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. 세련된 현장(프로젝트) 셀렉터 Banner
          InkWell(
            onTap: _showProjectBottomSheet,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1E293B), Color(0xFF334155)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF0F172A).withOpacity(0.15),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.location_city_rounded, color: Color(0xFF38BDF8), size: 24),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              '현재 현장',
                              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, fontWeight: FontWeight.w500),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                '진행중 🟢',
                                style: TextStyle(color: Color(0xFF34D399), fontSize: 10, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _selectedProject,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.unfold_more_rounded, color: Colors.white70),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 2. 3대 메인 카테고리 헤더
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                '핵심 서비스 카테고리',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF0F172A),
                  letterSpacing: -0.5,
                ),
              ),
              Text(
                '모듈 전체보기',
                style: TextStyle(fontSize: 12, color: Colors.blue[600], fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 3. 3대 대형 히어로 카테고리 카드 (Hero Category Cards)
          _buildHeroCategoryCard(
            title: '1. 업무 관리 (Work Core)',
            subtitle: '내 할당 업무 3건 | 진행 중 회의록 2건',
            badgeText: '업무 3',
            badgeColor: const Color(0xFF2563EB),
            gradientColors: [const Color(0xFFEFF6FF), const Color(0xFFDBEAFE)],
            iconBgColor: const Color(0xFF2563EB),
            icon: Icons.task_alt_rounded,
            borderColor: const Color(0xFFBFDBFE),
            onTap: () => setState(() => _selectedIndex = 1),
          ),
          const SizedBox(height: 12),

          _buildHeroCategoryCard(
            title: '2. 프로젝트 관리 (Project Core)',
            subtitle: '계약 현황 | 수납·입출금 | 현장 설정',
            badgeText: '계약 12건',
            badgeColor: const Color(0xFF059669),
            gradientColors: [const Color(0xFFECFDF5), const Color(0xFFD1FAE5)],
            iconBgColor: const Color(0xFF059669),
            icon: Icons.business_center_rounded,
            borderColor: const Color(0xFFA7F3D0),
            onTap: () => setState(() => _selectedIndex = 2),
          ),
          const SizedBox(height: 12),

          _buildHeroCategoryCard(
            title: '3. 전자 결재 (Approval Core)',
            subtitle: '미결함 5건 대기 중 | 결재 기안 및 승인',
            badgeText: '미결 5',
            badgeColor: const Color(0xFFD97706),
            gradientColors: [const Color(0xFFFFFBEB), const Color(0xFFFEF3C7)],
            iconBgColor: const Color(0xFFD97706),
            icon: Icons.draw_rounded,
            borderColor: const Color(0xFFFDE68A),
            onTap: () {},
          ),
          const SizedBox(height: 24),

          // 4. 공용 문서 퀵 가이드 바
          InkWell(
            onTap: () => setState(() => _selectedIndex = 3),
            borderRadius: BorderRadius.circular(12),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[200]!),
              ),
              child: Row(
                children: [
                  const Icon(Icons.folder_shared_rounded, color: Color(0xFF475569)),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '공용 문서 섹션 (Docs)',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                        ),
                        Text(
                          '전사 사규, 온보딩 가이드 및 현장 도면/서식 열람',
                          style: TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                        ),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right_rounded, color: Colors.grey[400]),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 5. 최근 현장 타임라인 요약
          const Text(
            '최근 현장 소식',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Color(0xFF0F172A),
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey[200]!),
            ),
            child: Column(
              children: [
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.work_outline, color: Color(0xFF2563EB), size: 20),
                  ),
                  title: const Text('101동 3층 골조 공사 점검', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                  subtitle: const Text('진척률: 70% | 담당자: 홍길동', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  trailing: const Text('오늘', style: TextStyle(fontSize: 11, color: Colors.grey)),
                ),
                Divider(height: 1, color: Colors.grey[100]),
                ListTile(
                  leading: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.purple[50],
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.groups_outlined, color: Colors.purple, size: 20),
                  ),
                  title: const Text('주간 공정 현황 및 안전 점검 회의', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                  subtitle: const Text('결정사항 3건 | 액션아이템 2건', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  trailing: const Text('어제', style: TextStyle(fontSize: 11, color: Colors.grey)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // 모던 대형 히어로 카테고리 카드 렌더링 헬퍼
  Widget _buildHeroCategoryCard({
    required String title,
    required String subtitle,
    required String badgeText,
    required Color badgeColor,
    required List<Color> gradientColors,
    required Color iconBgColor,
    required IconData icon,
    required Color borderColor,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: borderColor, width: 1),
          boxShadow: [
            BoxShadow(
              color: iconBgColor.withOpacity(0.06),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: iconBgColor,
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: iconBgColor.withOpacity(0.3),
                    blurRadius: 6,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Icon(icon, color: Colors.white, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF0F172A),
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: badgeColor,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          badgeText,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[700],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Icon(Icons.arrow_forward_ios_rounded, color: Colors.grey[500], size: 16),
          ],
        ),
      ),
    );
  }
}
