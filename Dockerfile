FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /Main-pj-AI-Service/app

# 3. pip 업그레이드 및 Poetry 설치 (설치 로그를 보기 쉽게 출력)
RUN pip install --upgrade pip && pip install poetry && poetry --version

# 4. Poetry 가상환경 설정을 전역 사용으로 변경
RUN poetry config virtualenvs.create false

# 5. 프로젝트 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# 6. Poetry를 사용하여 의존성 설치 (설치 과정 로그 출력)
RUN poetry install --no-interaction --no-root && poetry show django

# 프로젝트 파일 복사
COPY ../. .

# 포트 노출
EXPOSE 8000

# 명령어 실행
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
