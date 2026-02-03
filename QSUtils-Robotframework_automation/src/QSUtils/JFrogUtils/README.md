# JFrogUtils

JFrogUtils는 QSUtils 프로젝트에 JFrog Artifactory 파일 업로드 기능을 제공하는 패키지입니다. jfrog-cli를 래핑하여 사용하기 쉬운 Python 인터페이스를 제공하며, 자동 인증
확인과 권한 검증 기능을 포함합니다.

## 목표

- JFrog Artifactory에 파일/디렉토리 업로드 기능 제공
- 기존 jf-cli 인증 상태 확인 (`jf config show` 명령어로 확인)
- 리포지토리 접근 및 업로드 권한 확인
- 사용자 친화적인 에러 처리 및 가이드
- QSUtils 기존 아키텍처 패턴 준수

**중요**: 이 패키지는 인증을 직접 처리하지 않음. 기존에 설정된 jf-cli 인증 상태를 확인하고 권한을 검증하는 것이 주 목적.

## 고정 설정

- **서버 URL**: `https://bart.sec.samsung.net/artifactory`
- **기본 리포지토리**: `oneos-qsymphony-issues-generic-local`
- **서버 이름**: `qsutils-server`

## 설치 요구사항

### 시스템 의존성

1. **jfrog-cli 설치**
   ```bash
   # Linux/macOS
   curl -fL https://install-cli.jfrog.io | sh
   
   # 또는 수동 설치
   # JFrog 공식 문서 참조: https://jfrog.com/getcli/
   ```

2. **JFrog 인증 설정**
   ```bash
   # 서버 설정
   jf c add qsutils-server --url=https://bart.sec.samsung.net/artifactory
   
   # 로그인
   jf rt login qsutils-server
   ```

### Python 의존성

- QSUtils 프로젝트에 포함됨
- PySide6 (Dialog 기능 사용 시)

## 사용 방법

### 기본 사용법

```python
from QSUtils.JFrogUtils import JFrogManager

# 기본 설정으로 매니저 생성
jfrog = JFrogManager()

# 파일 업로드
result = jfrog.upload_file("/path/to/file.txt")
if result.success:
    print(f"업로드 성공: {result.data['uploaded_files'][0]['url']}")
else:
    print(f"업로드 실패: {result.message}")

# 디렉토리 업로드
result = jfrog.upload_directory("/path/to/directory")
if result.success:
    print(f"디렉토리 업로드 성공: {result.data['total_uploaded']}개 파일")
else:
    print(f"업로드 실패: {result.message}")
```

### Dialog와 함께 업로드

```python
from QSUtils.JFrogUtils import JFrogManager

jfrog = JFrogManager()

# Dialog와 함께 단일 파일 업로드
result = jfrog.upload_file_with_dialog("/path/to/file.txt", parent=self)

# Dialog와 함께 디렉토리 업로드
result = jfrog.upload_directory_with_dialog("/path/to/directory", parent=self)

if result.success:
    print("업로드 완료")
else:
    print(f"업로드 실패 또는 취소: {result.message}")
```

### 권한 확인

```python
from QSUtils.JFrogUtils import JFrogManager

jfrog = JFrogManager()

# 전체 설정 확인
result = jfrog.verify_setup()
if not result.success:
    print(f"설정 오류: {result.message}")
    return

# 권한만 확인
result = jfrog.check_permissions()
if not result.success:
    print(f"권한 오류: {result.message}")
    return

print("설정 및 권한 확인 완료")
```

### 설정 커스터마이징

```python
from QSUtils.JFrogUtils import JFrogManager, JFrogConfig

config = JFrogConfig(
    server_url="https://bart.sec.samsung.net/artifactory",
    default_repo="custom-repo",
    check_permissions=True
)

jfrog = JFrogManager(config)
result = jfrog.upload_file("/path/to/file.txt")
```

## API 참조

### JFrogManager

메인 JFrog 관리 클래스

#### 메소드

##### `verify_setup() -> JFrogOperationResult`

전체 설정 확인 (jf-cli 설치, 인증, 권한)

**반환값:**

- `success`: 설정 확인 성공 여부
- `message`: 결과 메시지
- `data`: 상세 정보

##### `check_permissions() -> JFrogOperationResult`

리포지토리 권한만 확인

##### `upload_file(local_path, target_path=None, repo=None) -> JFrogOperationResult`

단일 파일 업로드

**매개변수:**

- `local_path`: 업로드할 로컬 파일 경로
- `target_path`: 타겟 경로 (없으면 파일명 사용)
- `repo`: 리포지토리 (없으면 기본 리포지토리 사용)

##### `upload_directory(local_path, target_path=None, repo=None) -> JFrogOperationResult`

디렉토리 업로드 (재귀적)

**매개변수:**

- `local_path`: 업로드할 로컬 디렉토리 경로
- `target_path`: 타겟 경로 (없으면 디렉토리명 사용)
- `repo`: 리포지토리 (없으면 기본 리포지토리 사용)

##### `upload_file_with_dialog(local_path, target_path=None, repo=None, parent=None) -> JFrogOperationResult`

Dialog와 함께 단일 파일 업로드

**매개변수:**

- `local_path`: 업로드할 로컬 파일 경로
- `target_path`: 타겟 경로
- `repo`: 리포지토리
- `parent`: 부모 위젯

##### `upload_directory_with_dialog(local_path, target_path=None, repo=None, parent=None) -> JFrogOperationResult`

Dialog와 함께 디렉토리 업로드

**매개변수:**

- `local_path`: 업로드할 로컬 디렉토리 경로
- `target_path`: 타겟 경로
- `repo`: 리포지토리
- `parent`: 부모 위젯

### JFrogConfig

JFrog 설정 데이터클래스

```python
@dataclass
class JFrogConfig:
    server_url: str = "https://bart.sec.samsung.net/artifactory"
    default_repo: str = "oneos-qsymphony-issues-generic-local"
    server_name: str = "qsutils-server"
    upload_timeout: int = 300
    check_permissions: bool = True
```

### JFrogOperationResult

작업 결과 데이터클래스

```python
@dataclass
class JFrogOperationResult:
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
```

## Dialog 기능

JFrogUploadDialog는 업로드 진행 상태를 표시하는 모달 Dialog입니다.

### 기능

- 실시간 진행률 표시 (전체 및 현재 파일)
- 업로드 속도 및 예상 완료 시간
- 상세 로그 표시
- 일시정지/재개/취소 기능
- 자동 스크롤 로그

### 사용 예제

```python
# PySide6 애플리케이션에서
from QSUtils.JFrogUtils import JFrogManager

class MyWindow(QMainWindow):
    def upload_file(self):
        jfrog = JFrogManager()
        result = jfrog.upload_file_with_dialog(
            "/path/to/file.txt", 
            parent=self
        )
        
        if result.success:
            QMessageBox.information(self, "성공", "파일 업로드 완료")
        else:
            QMessageBox.warning(self, "실패", result.message)
```

## 에러 처리

### 일반적인 에러 시나리오

1. **jf-cli 설치되지 않음**
   ```
   jf-cli가 설치되지 않았습니다. JFrog 공식 문서를 참조하여 설치해주세요.
   ```

2. **인증 필요**
   ```
   JFrog에 먼저 로그인이 필요합니다. 'jf c add'와 'jf rt login'을 실행하세요.
   ```

3. **권한 없음**
   ```
   oneos-qsymphony-issues-generic-local 리포지토리에 업로드 권한이 없습니다. 관리자에게 문의하세요.
   ```

4. **리포지토리 없음**
   ```
   리포지토리를 찾을 수 없습니다: repository-name
   ```

### 예외 처리 예제

```python
from QSUtils.JFrogUtils import JFrogManager
from QSUtils.JFrogUtils.exceptions import (
    JFrogNotInstalledError,
    JFrogLoginRequiredError,
    JFrogPermissionDeniedError
)

jfrog = JFrogManager()

try:
    result = jfrog.upload_file("/path/to/file.txt")
    
    if not result.success:
        if isinstance(result.error, JFrogNotInstalledError):
            print("jf-cli를 설치해주세요")
        elif isinstance(result.error, JFrogLoginRequiredError):
            print("JFrog에 로그인해주세요")
        elif isinstance(result.error, JFrogPermissionDeniedError):
            print("권한이 없습니다")
        else:
            print(f"업로드 실패: {result.message}")
            
except Exception as e:
    print(f"예상치 못은 오류: {e}")
```

## 고급 기능

### 대형 파일 청크 업로드

100MB 이상의 파일은 자동으로 청크 업로드됩니다 (기본 10MB 청크).

```python
# 청크 업로드는 자동으로 처리됨
result = jfrog.upload_file("/path/to/large_file.zip")
```

### 백그라운드 업로드

Dialog를 사용하면 업로드가 백그라운드에서 처리되어 UI 응답성이 유지됩니다.

### 진행 상태 모니터링

```python
# Dialog 없이 진행 상태 모니터링
from QSUtils.JFrogUtils import JFrogUploader, JFrogConfig

config = JFrogConfig()
uploader = JFrogUploader(config)

# 업로드 ID로 진행 상태 조회
result = uploader.upload_file("/path/to/file.txt", upload_id="my_upload")
progress = uploader.get_upload_progress("my_upload")

if progress:
    print(f"진행률: {progress.progress_percentage:.1f}%")
    print(f"속도: {progress.speed_bps / 1024 / 1024:.1f} MB/s")
```

## 아키텍처

```
src/QSUtils/JFrogUtils/
├── __init__.py              # 패키지 초기화 및 주요 클래스 export
├── JFrogManager.py          # 메인 JFrog 관리 클래스
├── JFrogConfig.py           # JFrog 설정 관리
├── JFrogUploader.py         # 파일 업로드 전용 클래스
├── JFrogUploadWorker.py      # 백그라운드 업로드 Worker (QThread)
├── JFrogUploadDialog.py      # 업로드 진행 상태 Dialog
├── JFrogAuthManager.py      # 인증 관리 클래스
├── JFrogPermissionChecker.py # 권한 확인 클래스
└── exceptions.py            # JFrog 관련 예외 정의
```

## 테스트

```bash
# 단위 테스트 실행
cd /path/to/QSUtils
PYTHONPATH=src python -m pytest tests/test_jfrog_*.py -v

# 특정 테스트
PYTHONPATH=src python -m pytest tests/test_jfrog_uploader.py -v
PYTHONPATH=src python -m pytest tests/test_jfrog_manager.py -v
```

## 보안 고려사항

- JFrogUtils는 인증 정보를 저장하지 않음
- jf-cli가 관리하는 인증 정보만 사용
- 로그에 민감 정보 노출 방지
- HTTPS 통신만 사용

## 의존성

### 필수

- Python 3.8+
- jfrog-cli
- QSUtils

### 선택적

- PySide6 (Dialog 기능 사용 시)

## 라이선스

QSUtils 프로젝트 라이선스를 따릅니다.

## 기여

버그 리포트나 기능 요청은 QSUtils 프로젝트의 이슈 트래커를 통해 제출해주세요.

## 변경 로그

### v1.0.0

- 초기 릴리스
- 파일/디렉토리 업로드 기능
- Dialog 기반 진행 상태 표시
- jf-cli 래핑 및 권한 확인
- 63개 단위 테스트 케이스
