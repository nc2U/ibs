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

  // 선택된 프로젝트 (임시 초기값)
  String _selectedProject = '반포 아크로리버파크 신축공사';
  final List<String> _projectList = [
    '반포 아크로리버파크 신축공사',
    '성수 지식산업센터 건립공사',
    '해운대 오피스텔 분양사업',
  ];

  Future<void> _handleLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('로그아웃'),
        content: const Text('정말 로그아웃 하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('로그아웃', style: TextStyle(color: Colors.red)),
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
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: [
            Image.asset(
              'assets/images/logo.png',
              width: 28,
              height: 28,
            ),
            const SizedBox(width: 8),
            const Text(
              'IBS워크스페이스',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            tooltip: '알림',
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded),
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
        selectedItemColor: Colors.indigo,
        unselectedItemColor: Colors.grey[600],
        items: const [
          BottomNavigationBarTypeItem(
            icon: Icon(Icons.dashboard_rounded),
            label: '홈',
          ),
          BottomNavigationBarTypeItem(
            icon: Icon(Icons.assignment_turned_in_rounded),
            label: '업무',
          ),
          BottomNavigationBarTypeItem(
            icon: Icon(Icons.groups_rounded),
            label: '회의록',
          ),
          BottomNavigationBarTypeItem(
            icon: Icon(Icons.settings_rounded),
            label: '설정',
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
        return const Center(child: Text('업무 관리 (공사 예정)'));
      case 2:
        return const Center(child: Text('회의록 목록 (공사 예정)'));
      case 3:
        return const Center(child: Text('설정 (공사 예정)'));
      default:
        return _buildHomeTab();
    }
  }

  Widget _buildHomeTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. 현장 (프로젝트) 선택 셀렉터 카드
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.location_city_rounded, color: Colors.indigo[700], size: 20),
                      const SizedBox(width: 6),
                      Text(
                        '현재 선택된 현장',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: _selectedProject,
                      isExpanded: true,
                      icon: const Icon(Icons.arrow_drop_down_circle_outlined, color: Colors.indigo),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      onChanged: (String? newValue) {
                        if (newValue != null) {
                          setState(() {
                            _selectedProject = newValue;
                          });
                        }
                      },
                      items: _projectList.map<DropdownMenuItem<String>>((String value) {
                        return DropdownMenuItem<String>(
                          value: value,
                          child: Text(value),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // 2. 빠른 실행 메뉴 (Quick Menu Grid)
          const Text(
            '빠른 메뉴',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: [
              _buildQuickMenuItem(
                icon: Icons.task_alt_rounded,
                color: Colors.blue,
                label: '내 할당 업무',
                badgeCount: 3,
                onTap: () {
                  setState(() => _selectedIndex = 1);
                },
              ),
              _buildQuickMenuItem(
                icon: Icons.meeting_room_rounded,
                color: Colors.purple,
                label: '회의록/결정',
                badgeCount: 1,
                onTap: () {
                  setState(() => _selectedIndex = 2);
                },
              ),
              _buildQuickMenuItem(
                icon: Icons.draw_rounded,
                color: Colors.orange,
                label: '전자 결재',
                badgeCount: 5,
                onTap: () {},
              ),
              _buildQuickMenuItem(
                icon: Icons.camera_alt_rounded,
                color: Colors.teal,
                label: '현장 사진첨부',
                onTap: () {},
              ),
              _buildQuickMenuItem(
                icon: Icons.account_balance_wallet_rounded,
                color: Colors.green,
                label: '수납/지출 현황',
                onTap: () {},
              ),
              _buildQuickMenuItem(
                icon: Icons.description_rounded,
                color: Colors.indigo,
                label: '현장 문서함',
                onTap: () {},
              ),
            ],
          ),
          const SizedBox(height: 24),

          // 3. 최근 업무 및 회의 요약 카드
          const Text(
            '최근 현장 소식',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: ListView(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: const [
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.blueAccent,
                    child: Icon(Icons.work_outline, color: Colors.white, size: 20),
                  ),
                  title: Text('101동 3층 골조 공사 점검'),
                  subtitle: Text('담당자: 홍길동 | 진척률: 70%'),
                  trailing: Text('오늘', style: TextStyle(fontSize: 12, color: Colors.grey)),
                ),
                Divider(height: 1),
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.purpleAccent,
                    child: Icon(Icons.meeting_room, color: Colors.white, size: 20),
                  ),
                  title: Text('주간 공정 현황 및 안전 점검 회의'),
                  subtitle: Text('결정사항 3건 | 액션아이템 2건'),
                  trailing: Text('어제', style: TextStyle(fontSize: 12, color: Colors.grey)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickMenuItem({
    required IconData icon,
    required Color color,
    required String label,
    int badgeCount = 0,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircleAvatar(
                  radius: 22,
                  backgroundColor: color.withOpacity(0.12),
                  child: Icon(icon, color: color, size: 24),
                ),
                const SizedBox(height: 8),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
            if (badgeCount > 0)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.red,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '$badgeCount',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// BottomNavigationBarItem helper
class BottomNavigationBarTypeItem extends BottomNavigationBarItem {
  const BottomNavigationBarTypeItem({
    required super.icon,
    required super.label,
  });
}
