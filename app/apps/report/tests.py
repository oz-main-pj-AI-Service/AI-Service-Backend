# import uuid
#
# from apps.report.models import Report
# from django.contrib.auth import get_user_model
# from django.test import TestCase
#
# User = get_user_model()
# """
# - 테스트 리스트
#
# 1. 기본 데이터 테스트
# 2. Report 모델 생성 테스트
# 3. 관리자 응답이 포함된 Report 테스트
# 4. __str__ 메서드 테스트
# 5. 기본 정렬 순서(생성일 내림차순) 테스트
# 6. 상태 선택 옵션 테스트
# 7. 리포트 유형 선택 옵션 테스트
# 8. to_dict 메서드 테스트
# 9. 사용자 삭제 시 리포트도 삭제되는지 테스트 (CASCADE)
# 10. 관리자 삭제 시 admin_id만 NULL로 설정되는지 테스트 (SET_NULL)
#
# """
#
#
# class ReportModelTest(TestCase):
#     """Report 모델 테스트 클래스"""
#
#     def setUp(self):
#         """테스트에 필요한 데이터 설정"""
#         # 일반 사용자와 관리자 생성
#         self.user = User.objects.create_user(
#             email="test@test.com",
#             nickname="test",
#             password="test1234",
#             phone_number="1234",
#         )
#         self.super_user = User.objects.create_superuser(
#             email="admin_test@test.com",
#             nickname="admin_test",
#             password="test1234",
#         )
#
#         # 기본 테스트 데이터
#         self.title = "아니 식단 짤라다가 내 돈 다 빠져나갔네 돈내놓으셈 진짜"
#         self.description = "아니 식단 짤라고 식단 짤라그랫는데 내 돈 다빠져나갔잖아 ㅡㅡ 아 20분내로 해결하셈 백엔드놈들아"
#         self.report_type = Report.ReportType.ERROR
#
#     def test_create_report(self):
#         """Report 모델 생성 테스트"""
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#         )
#
#         # 데이터베이스에서 조회
#         saved_report = Report.objects.get(id=report.id)
#
#         # 기본 필드 검증
#         self.assertEqual(saved_report.user_id, self.user)
#         self.assertEqual(saved_report.title, self.title)
#         self.assertEqual(saved_report.description, self.description)
#         self.assertEqual(saved_report.type, self.report_type)
#         self.assertEqual(saved_report.status, Report.StatusType.OPEN)  # 기본값 확인
#         self.assertIsNone(saved_report.admin_comment)
#         self.assertIsNone(saved_report.admin_id)
#         self.assertIsNotNone(saved_report.created_at)
#
#         # UUID 형식 검증
#         self.assertIsInstance(saved_report.id, uuid.UUID)
#
#     def test_report_with_admin_response(self):
#         """관리자 응답이 포함된 Report 테스트"""
#         admin_comment = "진짜 죄송합니다.. 당신의 돈은 제것입니다.."
#
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#             status=Report.StatusType.IN_PROGRESS,
#             admin_comment=admin_comment,
#             admin_id=self.super_user,
#         )
#
#         saved_report = Report.objects.get(id=report.id)
#         self.assertEqual(saved_report.status, Report.StatusType.IN_PROGRESS)
#         self.assertEqual(saved_report.admin_comment, admin_comment)
#         self.assertEqual(saved_report.admin_id, self.super_user)
#
#     def test_report_str_method(self):
#         """__str__ 메서드 테스트"""
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#         )
#
#         expected_str = f"{self.title} ({self.report_type}) - {Report.StatusType.OPEN}"
#         self.assertEqual(str(report), expected_str)
#
#     def test_report_ordering(self):
#         """기본 정렬 순서(생성일 내림차순) 테스트"""
#         # 첫 번째 리포트 생성
#         first_report = Report.objects.create(
#             user_id=self.user,
#             title="첫 번째 보고서",
#             description="설명...",
#             type=Report.ReportType.ERROR,
#         )
#
#         # 잠시 대기 후 두 번째 리포트 생성
#         import time
#
#         time.sleep(0.1)  # 100ms 대기
#
#         second_report = Report.objects.create(
#             user_id=self.user,
#             title="두 번째 보고서",
#             description="설명...",
#             type=Report.ReportType.QUESTION,
#         )
#
#         # 모든 리포트 조회 (기본 정렬 순서 적용)
#         reports = list(Report.objects.all())
#
#         # 최신 리포트가 먼저 나와야 함
#         self.assertEqual(reports[0], second_report)
#         self.assertEqual(reports[1], first_report)
#
#     def test_report_status_choices(self):
#         """상태 선택 옵션 테스트"""
#         # 상태 변경 테스트
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#         )
#
#         # 기본값 확인
#         self.assertEqual(report.status, Report.StatusType.OPEN)
#
#         # 상태 변경
#         report.status = Report.StatusType.IN_PROGRESS
#         report.save()
#         self.assertEqual(
#             Report.objects.get(id=report.id).status, Report.StatusType.IN_PROGRESS
#         )
#
#         report.status = Report.StatusType.RESOLVED
#         report.save()
#         self.assertEqual(
#             Report.objects.get(id=report.id).status, Report.StatusType.RESOLVED
#         )
#
#         report.status = Report.StatusType.CLOSED
#         report.save()
#         self.assertEqual(
#             Report.objects.get(id=report.id).status, Report.StatusType.CLOSED
#         )
#
#     def test_report_type_choices(self):
#         """리포트 유형 선택 옵션 테스트"""
#         # 각 유형별 리포트 생성 테스트
#         error_report = Report.objects.create(
#             user_id=self.user,
#             title="오류 보고",
#             description="설명...",
#             type=Report.ReportType.ERROR,
#         )
#         self.assertEqual(error_report.type, Report.ReportType.ERROR)
#
#         question_report = Report.objects.create(
#             user_id=self.user,
#             title="질문",
#             description="설명...",
#             type=Report.ReportType.QUESTION,
#         )
#         self.assertEqual(question_report.type, Report.ReportType.QUESTION)
#
#         feature_report = Report.objects.create(
#             user_id=self.user,
#             title="기능 요청",
#             description="설명...",
#             type=Report.ReportType.FEATURE_REQUEST,
#         )
#         self.assertEqual(feature_report.type, Report.ReportType.FEATURE_REQUEST)
#
#         other_report = Report.objects.create(
#             user_id=self.user,
#             title="기타",
#             description="설명...",
#             type=Report.ReportType.OTHER,
#         )
#         self.assertEqual(other_report.type, Report.ReportType.OTHER)
#
#     def test_to_dict_method(self):
#         """to_dict 메서드 테스트"""
#         # 관리자 응답이 포함된 리포트 생성
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#             status=Report.StatusType.RESOLVED,
#             admin_comment="문제가 해결되었습니다.",
#             admin_id=self.super_user,
#         )
#
#         # to_dict 메서드 호출
#         report_dict = report.to_dict()
#
#         # 딕셔너리 형태 검증
#         self.assertEqual(report_dict["id"], str(report.id))
#         self.assertEqual(report_dict["user_id"], str(self.user.id))
#         self.assertEqual(report_dict["title"], self.title)
#         self.assertEqual(report_dict["description"], self.description)
#         self.assertEqual(report_dict["status"], Report.StatusType.RESOLVED)
#         self.assertEqual(report_dict["type"], self.report_type)
#         self.assertEqual(report_dict["admin_comment"], "문제가 해결되었습니다.")
#         self.assertEqual(report_dict["admin_id"], str(self.super_user.id))
#         self.assertIsInstance(report_dict["created_at"], str)  # ISO 형식 문자열 확인
#
#     def test_delete_admin_sets_null(self):
#         """관리자 삭제 시 admin_id만 NULL로 설정되는지 테스트 (SET_NULL)"""
#         # 관리자 응답이 포함된 리포트 생성
#         report = Report.objects.create(
#             user_id=self.user,
#             title=self.title,
#             description=self.description,
#             type=self.report_type,
#             admin_comment="답변입니다.",
#             admin_id=self.super_user,
#         )
#
#         report_id = report.id
#
#         # 관리자 삭제
#         self.super_user.delete()
#
#         # 리포트는 유지되고 admin_id만 NULL로 설정되었는지 확인
#         updated_report = Report.objects.get(id=report_id)
#         self.assertEqual(updated_report.admin_comment, "답변입니다.")  # 코멘트는 유지됨
