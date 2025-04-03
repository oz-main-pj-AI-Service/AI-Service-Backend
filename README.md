
# 🥘 한상비서 AI (Hansang Assistant AI)

> 사용자의 기호와 건강 정보를 기반으로 식단, 음식, 레시피를 AI가 추천해주는 맞춤형 가상 식사 비서 서비스

---

## 🧠 주요 기능

- **AI 기반 추천 시스템**
  - 레시피 추천
  - 건강 식단 추천
  - 일반 음식 추천
- **실시간 스트리밍 응답 처리 (SSE)**
- **활동 로그 저장 및 조회**
- **JWT + 소셜 로그인 (Google, Naver)**
- **관리자 기능: 사용자 관리, 문의 답변 등**

---

## ⚙️ 기술 스택

### Back-End

- `Python 3`, `Django`, `Django REST Framework`
- `Redis` – 브루트포스 방지, 토큰 관리, 요청 제한
- `Gunicorn` – Django WSGI 서버
- `Nginx` – 리버스 프록시 + 정적 파일 서빙
- `Docker`, `Docker Compose` – 서비스 컨테이너화
- `PostgreSQL (RDS)`
- `Google Gemini API` – 생성형 AI 기능
- `drf-yasg` – Swagger 기반 API 문서화
- `Pytest`, `unittest.mock` – 테스트 및 외부 API 모킹
- `GitHub Actions` – CI/CD 자동화

### Front-End

- `React`, `TypeScript`, `Vite`
- `TailwindCSS`, `shadcn/ui`
- `TanStack Query`, `Axios`, `Zod`, `React Hook Form`
- `Zustand` – 상태 관리
- `SSE 기반 스트리밍 응답 처리`

---

## 🛠️ 시스템 아키텍처

```
[Client] ⇄ Nginx ⇄ Gunicorn ⇄ Django ⇄ Redis/PostgreSQL
                          ⇅
                    Gemini API (AI 응답)
```

---

## 🚀 배포 인프라

- **AWS EC2 + Route53 + SSL (Let's Encrypt + Certbot)**
- **Docker 기반 멀티 컨테이너 구성**
- `docker-compose`로 Nginx, Django, Redis 통합
- 프론트/백엔드 서브도메인 분리 (`hansang.ai.kr`, `api.hansang.ai.kr`)
- **CI/CD**: `release` 브랜치에 push → Docker 이미지 빌드 & Docker Hub 푸시 → EC2 자동 배포

---

## 🧪 테스트

- `pytest` 기반 자동 테스트 수행
- Gemini API 호출은 `mock` 처리하여 테스트 비용 및 시간 절감
- `APITestCase`로 REST API 단위 테스트 구현

---

## 📂 디렉토리 구조 (Back-End)

```
.
├── app/
│   ├── user/
│   ├── report/
│   ├── ai/
│   ├── log/
│   └── common/
├── config/
│   ├── settings/
│   └── urls.py
├── Dockerfile
├── docker-compose.yml
├── nginx/
│   └── default.conf
└── manage.py
```

---

## 👥 팀원 구성

| 이름     | 역할                         |
|----------|------------------------------|
| 김병학   | 🧠 Back-End 팀장, CI/CD 구축, EC2 배포, 코드 전체 리뷰 |
| 김이준   | 백엔드 API, Gemini 연동, 리포트 기능 개발 |
| 나기태   | 프론트 팀장, 메인/관리자 페이지, 배포 |
| 김유주   | 프론트 기능 개발, 인증 로직, 소셜 로그인 |

---

## 📎 주요 링크

- 🖥️ 배포 주소: [https://hansang.ai.kr](https://hansang.ai.kr)
- 🧪 API 문서 (Swagger): `https://api.hansang.ai.kr/swagger/`
- 
---

© 2025 한상비서 AI - OZ코딩스쿨 NEXT.RUNNERS