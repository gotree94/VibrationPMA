# 실험 환경(개발 환경) 구축 가이드

본 문서는 **PC(학습·검증) 환경**과 **MCU(STM32) 배포 환경**을 처음부터 구축하는 절차를 상세히 다룬다. 운영체제는 Windows 10/11을 기준으로 한다.

---

## 1. PC 환경 구축 (Python · TensorFlow)

### 1.1 Python 및 가상환경 도구 설치

**옵션 A: Miniconda (권장)**

Miniconda는 파이썬과 패키지 관리를 한 번에 처리한다. 아래 링크에서 설치한다.
- https://docs.conda.io/en/latest/miniconda.html (Windows 64-bit 설치 프로그램)

설치 후 Anaconda Prompt(또는 PowerShell + conda)에서:

```powershell
conda create -n vibai python=3.11 -y
conda activate vibai
```

**옵션 B: 순수 Python**

이미 Python이 설치되어 있다면 venv 사용:

```powershell
python -m venv vibai
.\vibai\Scripts\Activate.ps1
```

### 1.2 필수 패키지 설치

```powershell
pip install --upgrade pip

# 딥러닝
pip install tensorflow==2.15.0

# 데이터 처리
pip install numpy pandas scipy scikit-learn

# 시각화
pip install matplotlib seaborn

# 개발/노트북
pip install jupyter ipykernel

# (선택) GPU 가속 - CUDA/cuDNN 자동 일치
# pip install tensorflow[and-cuda]
```

검증:

```python
import tensorflow as tf
print(tf.__version__)          # 2.15.0
print(tf.config.list_physical_devices('GPU'))  # GPU 장치 목록
```

### 1.3 프로젝트 디렉터리 생성

```powershell
# 이미 C:\VibrationPMA 를 만들었다면 생략
New-Item -ItemType Directory -Force -Path "C:\VibrationPMA\data"
New-Item -ItemType Directory -Force -Path "C:\VibrationPMA\models"
New-Item -ItemType Directory -Force -Path "C:\VibrationPMA\tflite_models"
New-Item -ItemType Directory -Force -Path "C:\VibrationPMA\results"
```

JPEG 파일, `pathlib`을 사용한 데이터 로딩을 위해 스크립트는 `code/` 하위에 배치한다.

---

## 2. STM32 무료 툴체인 설치 (MCU 배포용)

STMicro 소프트웨어는 아래 사이트에서 무료로 받을 수 있다 (계정 생성 필요, 무료).

### 2.1 STM32CubeIDE

통합 개발 환경(코드 편집 + 컴파일 + 디버깅 + 플래싱). **C/C++ 개발을 위해 반드시 필요.**

- 다운로드: https://www.st.com/en/development-tools/stm32cubeide.html
- 설치: 기본 옵션으로 진행. installers(아카이브)가 아닌 별도 설치 파일을 받아 설치.

> 참고: 일부 기능은 안정 버전보다 최신인 경우가 있으므로, 가능한 최신 안정 버전을 받는 것이 좋다. 버전이 오래되면 아래 X-CUBE-AI와의 호환 문제가 생길 수 있다. → 설치 후 Help > Update Software 로 최신화 권장.

### 2.2 STM32CubeMX

MCU 초기화 코드 생성 도구. **X-CUBE-AI(모델 → C 코드)를 연동**하기 위해 사용한다.

- 다운로드: https://www.st.com/en/development-tools/stm32cubemx.html
- Java(OpenJDK) 필요할 수 있음 — 설치 마법사가 안내함.

### 2.3 X-CUBE-AI (STM32Cube.AI)

STM의 AI 모델 최적화·배포 툴. **TFLite(FP32/int8) 모델을 STM32 전용 C 코드로 변환**한다.

- 다운로드: https://www.st.com/en/embedded-software/x-cube-ai.html
- 최신 버전: X-CUBE-AI v9/v10 (및 STM32Cube AI Studio v1.x 신형 툴)

> **신형 권장**: 기존 X-CUBE-AI 플러그인 대신 **STM32Cube AI Studio** 사용을 권장한다(신규 개발용). 다만 기존 X-CUBE-AI(STM32CubeMX 플러그인)도 여전히 동작하므로, 편의에 따라 선택한다.

설치 위치: `C:\Users\<사용자>\STM32Cube\Repository\Packs\STMicroelectronics\X-CUBE-AI\9.x.x`

### 2.4 STM32CubeProgrammer (선택, 플래싱용)

커맨드라인/그래픽으로 MCU에 펌웨어를 쓸 수 있는 도구.

- 다운로드: https://www.st.com/en/development-tools/stm32cubeprog.html

### 2.5 (선택) 진동 센서 보드

- 예: STEVAL-PROTEUS1(ISM330DHCX 내장), LIS3DSH, ADXL345 모듈
- NUCLEO 보드 + 외부 가속도계 모듈을 SPI/I2C로 연결

---

## 3. 툴 간 호환성 주의사항

| 조합 | 주의 |
|---|---|
| TensorFlow 2.15 ↔ X-CUBE-AI v9.x | X-CUBE-AI는 Keras/TFLite 플랫폼별 ops를 지원. Keras 3의 경우 `.keras` 포맷 사용 또는 `h5`/`tflite` 변환 필요 |
| int8 TFLite | X-CUBE-AI는 int8 모델 지원. ST 8비트 인증/검증 권장 |
| STM32CubeIDE 버전 | 오래된 버전은 새 X-CUBE-AI 팩과 호환 안 될 수 있음 → Software Update 수행 |

---

## 4. 가상환경 실행 요약 (매번 시작 시)

```powershell
conda activate vibai
cd C:\VibrationPMA
jupyter notebook   # 또는 code .
```

---

## 5. 설치 검증 체크리스트

- [ ] `conda env list` 에 `vibai` 확인
- [ ] `python -c "import tensorflow as tf; print(tf.__version__)"` → 2.x
- [ ] STM32CubeIDE 실행 → 새 프로젝트 생성 가능
- [ ] STM32CubeMX 실행 가능
- [ ] X-CUBE-AI 또는 STM32Cube AI Studio에서 `.tflite` 로딩 시도

---

## 6. 문제 해결 (FAQ)

**Q. GPU가 안 잡혀요.**
- NVIDIA 드라이버 설치, `pip install tensorflow[and-cuda]`, PowerShell에서 재실행.
- GPU가 없어도 CPU로 학습 가능(다만 느림).

**Q. `tflite` 변환 시 양자화 오류가 나요.**
- `representative_dataset`가 float32 numpy 배열을 만들어야 한다. `target_spec`, `supported_ops` 설정 확인.

**Q. STM32CubeIDE에서 X-CUBE-AI 팩이 보이지 않아요.**
- Help > Manage Embedded Software Packages > STMicroelectronics > X-CUBE-AI 설치 확인.
- `STM32CubeIDE` 최신 버전으로 업데이트.
