from apps.report.models import Report
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ReportListCreateView(APIView):
    """리포트 목록 조회 및 생성 API"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """리포트 목록 조회"""
        try:
            # 사용자 권한에 따른 필터링
            reports = Report.objects.filter(user_id=request.user)

            # 응답 데이터 생성
            response_data = [report.to_dict() for report in reports]
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # 서버 오류 처리
            return Response(
                {"error": "SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        """리포트 생성"""
        try:
            # 필수 필드 확인
            required_fields = ["title", "description", "type"]
            for field in required_fields:
                if field not in request.data:
                    return Response(
                        {
                            "error": "MISSING_FIELD",
                            "message": "필수 필드가 누락되었습니다.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # 제목 길이 검증
            if len(request.data["title"]) > 100:
                return Response(
                    {
                        "error": "TITLE_TOO_LONG",
                        "message": "제목은 100자 이내로 작성해주세요.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 타입 유효성 검증
            valid_types = [choice[0] for choice in Report.ReportType.choices]
            if request.data["type"] not in valid_types:
                return Response(
                    {
                        "error": "INVALID_TYPE",
                        "message": "유효하지 않은 리포트 타입입니다.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 리포트 생성
            report = Report(
                user_id=request.user,
                title=request.data["title"],
                description=request.data["description"],
                type=request.data["type"],
                status=Report.StatusType.OPEN,
            )
            report.save()

            # 응답 데이터 생성
            return Response(report.to_dict(), status=status.HTTP_201_CREATED)

        except Exception as e:
            # 서버 오류 처리
            return Response(
                {"error": "SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReportDetailView(APIView):
    """리포트 상세 조회, 수정, 삭제 API"""

    permission_classes = [IsAuthenticated]

    def get_report(self, id, user):
        """리포트 조회 및 권한 확인"""
        report = get_object_or_404(Report, id=id)

        # 사용자가 리포트 소유자인지 확인
        if report.user_id != user:
            return None, Response(
                {"error": "FORBIDDEN", "message": "접근 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return report, None

    def get(self, request, id):
        """리포트 상세 조회"""
        try:
            report, error_response = self.get_report(id, request.user)
            if error_response:
                return error_response

            return Response(report.to_dict(), status=status.HTTP_200_OK)

        except Report.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": "리포트를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            # 서버 오류 처리
            return Response(
                {"error": "SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, id):
        """리포트 수정"""
        try:
            report, error_response = self.get_report(id, request.user)
            if error_response:
                return error_response

            # 상태 확인 - OPEN 상태만 수정 가능
            if report.status != Report.StatusType.OPEN:
                return Response(
                    {
                        "error": "REPORT_LOCKED",
                        "message": "이미 처리가 시작된 리포트는 수정할 수 없습니다.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 필수 필드 확인
            required_fields = ["title", "description", "type"]
            for field in required_fields:
                if field not in request.data:
                    return Response(
                        {
                            "error": "MISSING_FIELD",
                            "message": "필수 필드가 누락되었습니다.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # 제목 길이 검증
            if len(request.data["title"]) > 100:
                return Response(
                    {
                        "error": "TITLE_TOO_LONG",
                        "message": "제목은 100자 이내로 작성해주세요.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 타입 유효성 검증
            valid_types = [choice[0] for choice in Report.ReportType.choices]
            if request.data["type"] not in valid_types:
                return Response(
                    {
                        "error": "INVALID_TYPE",
                        "message": "유효하지 않은 리포트 타입입니다.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 리포트 업데이트
            report.title = request.data["title"]
            report.description = request.data["description"]
            report.type = request.data["type"]

            # 저장
            report.save()

            # 응답 데이터 생성
            response_data = {
                "id": str(report.id),
                "title": report.title,
                "description": report.description,
                "type": report.type,
                "updated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Report.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": "리포트를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            # 서버 오류 처리
            return Response(
                {"error": "SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, id):
        """리포트 삭제"""
        try:
            report, error_response = self.get_report(id, request.user)
            if error_response:
                return error_response

            # 리포트 삭제
            deleted_at = timezone.now()
            report.delete()

            # 응답 데이터 생성
            response_data = {
                "id": str(id),
                "deleted_at": deleted_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Report.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": "리포트를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            # 서버 오류 처리
            return Response(
                {"error": "SERVER_ERROR", "message": "서버 내부 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
