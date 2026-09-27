import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ibs/core/models/user_model.dart';

void main() {
  group('UserModel & ProfileModel Serialization & Logic Test', () {
    test('ProfileModel fromJson & toJson matches data correctly', () {
      final json = {
        'pk': 1,
        'name': '홍길동',
        'birth_date': '1990-01-01',
        'cell_phone': '010-1234-5678',
        'image': 'https://example.com/avatar.png',
        'sign_image': 'https://example.com/sign.png',
        'sign_type': 'STAMP',
        'auto_watch_created': true,
        'auto_watch_assigned': false,
        'meeting_created_notification': true,
        'meeting_confirmed_notification': false,
      };

      final profile = ProfileModel.fromJson(json);

      expect(profile.pk, 1);
      expect(profile.name, '홍길동');
      expect(profile.cellPhone, '010-1234-5678');
      expect(profile.autoWatchAssigned, false);
      expect(profile.meetingConfirmedNotification, false);

      final convertedJson = profile.toJson();
      expect(convertedJson['name'], '홍길동');
      expect(convertedJson['birth_date'], '1990-01-01');
    });

    test('UserModel displayName and initial tests', () {
      final userWithProfile = UserModel.fromJson({
        'pk': 10,
        'username': 'gildong',
        'email': 'gildong@example.com',
        'is_active': true,
        'is_superuser': true,
        'profile': {
          'pk': 1,
          'name': '홍길동',
        },
      });

      expect(userWithProfile.displayName, '홍길동 (gildong)');
      expect(userWithProfile.nameOrUsername, '홍길동');
      expect(userWithProfile.initial, '홍');
      expect(userWithProfile.isSuperuser, true);

      final userWithoutProfile = UserModel.fromJson({
        'pk': 11,
        'username': 'admin',
        'is_active': true,
      });

      expect(userWithoutProfile.displayName, 'admin');
      expect(userWithoutProfile.nameOrUsername, 'admin');
      expect(userWithoutProfile.initial, 'A');
      expect(userWithoutProfile.isSuperuser, false);
    });
  });
}
