import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
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

  Future<void> _handleLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('로그아웃', style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('IBS 워크스페이스에서 로그아웃 하시겠습니까?'),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF202336), // 웹 사이드바 브랜드 컬러
      appBar: AppBar(
        backgroundColor: const Color(0xFF202336),
        foregroundColor: Colors.white,
        elevation: 0,
        titleSpacing: 20,
        title: Row(
          children: [
            SvgPicture.asset(
              'assets/images/sygnet.svg',
              width: 28,
              height: 28,
            ),
            const SizedBox(width: 10),
            const Text(
              'IBS 워크스페이스',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.5,
                color: Colors.white,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded, size: 24, color: Colors.white70),
            tooltip: '알림',
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, size: 22, color: Colors.white70),
            tooltip: '로그아웃',
            onPressed: _handleLogout,
          ),
          const SizedBox(width: 8),
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
        backgroundColor: const Color(0xFF191B2B), // 약간 더 짙은 하단바
        selectedItemColor: const Color(0xFF38BDF8),
        unselectedItemColor: const Color(0xFF787F9A),
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
        elevation: 12,
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
            icon: Icon(Icons.draw_rounded),
            label: '전자결재',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.folder_shared_rounded),
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
        return const Center(child: Text('업무 관리 (Issue / Meeting)', style: TextStyle(color: Colors.white)));
      case 2:
        return const Center(child: Text('프로젝트 관리 (Contract / Ledger)', style: TextStyle(color: Colors.white)));
      case 3:
        return const Center(child: Text('전자 결재 (Approval Core)', style: TextStyle(color: Colors.white)));
      case 4:
        return const Center(child: Text('공용 문서 섹션 (Docs)', style: TextStyle(color: Colors.white)));
      default:
        return _buildHomeTab();
    }
  }

  Widget _buildHomeTab() {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 3대 핵심 카테고리 대형 직사각형 히어로 카드들 (여백 최소화, 시원한 크기)
              _buildCategoryHeroCard(
                categoryNum: '01',
                title: '업무 관리',
                englishTitle: 'WORK CORE',
                description: '현장 업무 이슈, 회의록, 액션아이템 및 공정 진척률',
                icon: Icons.task_alt_rounded,
                accentColor: const Color(0xFF38BDF8), // Light Electric Blue
                gradientColors: [
                  const Color(0xFF1E3A8A), // Deep Sapphire Blue
                  const Color(0xFF2A2E47), // #202336과 어우러지는 카드 베이스
                ],
                badgeText: '할당 업무 3건',
                onTap: () => setState(() => _selectedIndex = 1),
              ),
              const SizedBox(height: 12),

              _buildCategoryHeroCard(
                categoryNum: '02',
                title: '프로젝트 관리',
                englishTitle: 'PROJECT CORE',
                description: '현장 선택, 계약 현황, 수납/입출금 및 현장 설정',
                icon: Icons.business_center_rounded,
                accentColor: const Color(0xFF34D399), // Emerald Green
                gradientColors: [
                  const Color(0xFF064E3B), // Deep Forest Emerald
                  const Color(0xFF2A2E47),
                ],
                badgeText: '계약 12건',
                onTap: () => setState(() => _selectedIndex = 2),
              ),
              const SizedBox(height: 12),

              _buildCategoryHeroCard(
                categoryNum: '03',
                title: '전자 결재',
                englishTitle: 'APPROVAL CORE',
                description: '미결함 결재 승인/반려, 기안함 및 모바일 서명',
                icon: Icons.draw_rounded,
                accentColor: const Color(0xFFFBBF24), // Amber Gold
                gradientColors: [
                  const Color(0xFF78350F), // Deep Warm Amber
                  const Color(0xFF2A2E47),
                ],
                badgeText: '미결 5건',
                onTap: () => setState(() => _selectedIndex = 3),
              ),
              const SizedBox(height: 16),

              // 하단 공용 문서 (Docs) 퀵 바
              InkWell(
                onTap: () => setState(() => _selectedIndex = 4),
                borderRadius: BorderRadius.zero,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2A2E47),
                    borderRadius: BorderRadius.zero,
                    border: Border.all(color: const Color(0xFF3B4061), width: 1),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF334155),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.folder_shared_rounded, color: Color(0xFF94A3B8), size: 22),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '공용 문서 섹션 (Docs)',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              '전사 사규, 온보딩 가이드 및 공통 서식/도면 열람',
                              style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios_rounded, color: Color(0xFF64748B), size: 16),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],
          ),
        );
      },
    );
  }

  // 3대 핵심 카테고리 대형 직사각형 히어로 카드 위젯
  Widget _buildCategoryHeroCard({
    required String categoryNum,
    required String title,
    required String englishTitle,
    required String description,
    required IconData icon,
    required Color accentColor,
    required List<Color> gradientColors,
    required String badgeText,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.zero,
      child: Container(
        height: 140, // 큼직하고 시원한 높이
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: gradientColors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.zero,
          border: Border.all(color: accentColor.withOpacity(0.3), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Stack(
          children: [
            // 은은하게 배경에 깔리는 대형 번호 표기 (01, 02, 03)
            Positioned(
              right: -10,
              bottom: -20,
              child: Text(
                categoryNum,
                style: TextStyle(
                  fontSize: 90,
                  fontWeight: FontWeight.w900,
                  color: Colors.white.withOpacity(0.04),
                  letterSpacing: -4,
                ),
              ),
            ),

            // 내용 구성
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: accentColor.withOpacity(0.15),
                            borderRadius: BorderRadius.zero,
                            border: Border.all(color: accentColor.withOpacity(0.3)),
                          ),
                          child: Icon(icon, color: accentColor, size: 24),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              englishTitle,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w800,
                                color: accentColor,
                                letterSpacing: 1.2,
                              ),
                            ),
                            Text(
                              title,
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                                letterSpacing: -0.5,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    // 우측 상단 배지
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: accentColor.withOpacity(0.2),
                        borderRadius: BorderRadius.zero,
                        border: Border.all(color: accentColor.withOpacity(0.5)),
                      ),
                      child: Text(
                        badgeText,
                        style: TextStyle(
                          color: accentColor,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Text(
                        description,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Color(0xFFCBD5E1),
                          fontWeight: FontWeight.w400,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Icon(
                      Icons.arrow_forward_rounded,
                      color: accentColor,
                      size: 20,
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
