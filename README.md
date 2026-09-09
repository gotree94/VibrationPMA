# 진동 신호 기반 예지보전 시스템의 엣지 AI(MCU) 구현

**회전기계 진동 데이터를 이용한 이상 진단 · 분류 모델과 STM32 MCU 엣지 AI 배포에 관한 연구**

> 본 문서는 석사학위 논문 수준의 완성도를 목표로, 데이터 획득(공개 데이터셋) → 전처리 → 특징 추출 → 딥러닝 학습(PC) → TFLite 변환·양자화 → PC 검증 → STM32Cube.AI 기반 MCU 배포(NUCLEO-F411RE / NUCLEO-H753ZI) → 실시간 추론 → 성능 분석 까지의 전 과정을 **실습 가능한 예제와 함께** 기술한다.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [데이터셋 조사 및 선정](#2-데이터셋-조사-및-선정)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [실험 환경(개발 환경) 구축](#4-실험-환경-구축)
5. [데이터 획득 및 전처리](#5-데이터-획득-및-전처리)
6. [특징 추출 및 데이터셋 구성](#6-특징-추출-및-데이터셋-구성)
7. [딥러닝 모델 설계 및 학습(PC)](#7-딥러닝-모델-설계-및-학습-pc)
8. [모델 변환 및 양자화(TFLite)](#8-모델-변환-및-양자화-tflite)
9. [PC에서의 추론 검증](#9-pc에서의-추론-검증)
10. [STM32Cube.AI 기반 MCU 배포](#10-stm32cubeai-기반-mcu-배포)
11. [실시간 추론 및 결과 해석](#11-실시간-추론-및-결과-해석)
12. [논문 작성 가이드](#12-논문-작성-가이드)
13. [참고문헌](#13-참고문헌)

---

## 1. 프로젝트 개요

### 1.1 연구 배경 및 필요성

회전기계(펌프, 모터, 압축기, 베어링 등)는 산업 설비의 핵심 구성요소로, 이들 장비에서 발생하는 **진동(vibration)**은 베어링 마모, 정렬 불량, 불평형(불균형), 윤활 불량 등 다양한 결함 신호를 포함한다. 진동 신호의 시계열 패턴을 분석하면 장비의 이상을 조기에 감지할 수 있으며, 이를 통해 **예지보전(Predictive Maintenance, PM)**이 가능해진다.

전통적인 예지보전은 시간 영역·주파수 영역의 통계적 특징을 수동으로 설계하고(Feature Engineering) 이를 SVM, k-NN, Random Forest 등의 머신러닝 분류기에 입력하는 방식이 주를 이루었다. 그러나 최근에는 시계열 데이터를 그대로 입력으로 사용하는 **딥러닝(1D-CNN, LSTM, TCN 등)** 기반의 자동 특징 추출 방식이 높은 정확도로 우수한 성능을 보여주고 있다.

한편, 산업 현장에서는 **데이터 보안, 통신 지연, 대역폭 제한** 등의 이유로 모든 데이터를 클라우드로 전송하는 것이 어려운 경우가 많다. 따라서 센서가 부착된 장비 근처의 **엣지 디바이스(Edge Device)**에서 실시간으로 추론하는 **엣지 AI(TinyML)** 기술이 주목받고 있다. 본 연구에서는 저전력·저비용의 MCU(Microcontroller Unit)인 **STM32(NUCLEO-F411RE, NUCLEO-H753ZI)** 위에서 진동 기반 딥러닝 모델을 동작시켜, PC 수준의 정확도를 유지하면서도 장비 인근에서 실시간으로 정상/이상을 분류할 수 있는 시스템을 구현한다.

### 1.2 연구 목표

1. 신뢰성 있는 공개 진동 데이터셋(CWRU, NASA IMS, Paderborn, XJTU-SY 등)을 획득·비교 분석한다.
2. 시계열 진동 데이터를 전처리하고 1D-CNN 기반 분류 모델을 설계·학습하여 PC에서 정상/이상(및 결함 유형)을 분류한다.
3. 학습된 모델을 **TFLite(정수 양자화, int8)**로 변환하여 PC에서 검증한다.
4. STM32Cube.AI(X-CUBE-AI)를 이용하여 변환 모델을 MCU 최적화 C 코드로 생성하고 **NUCLEO-F411RE / NUCLEO-H753ZI**에 배포한다.
5. 실제 MCU에서의 추론을 수행하고, **정확도, 추론 시간, 메모리(Flash/RAM) 사용량, 전력 소모**를 측정·분석한다.

### 1.3 기대 효과

- 클라우드 의존 없이 장비 인근에서 실시간 이상 탐지 가능
- 통신 부하 및 데이터 전송 비용 절감
- 조기 이상 감지를 통한 설비 가동 중단(downtime) 및 유지보수 비용 절감
- 저비용 MCU 기반 솔루션으로 폭넓은 보급 가능성 확보

---

## 2. 데이터셋 조사 및 선정

> **상세한 데이터셋별 특징, 다운로드 링크, 인용 형식은 [docs/02_datasets.md](docs/02_datasets.md)을 참고하라.**

본 과제에서는 학술적으로 가장 널리 사용되며 검증된 공개 베어링 진동 데이터셋을 여러 개 조사하고, 각각의 특성에 따라 적절한 실험을 설계한다.

### 2.1 후보 데이터셋 요약

| 데이터셋 | 제공기관 | 샘플링률 | 주요 내용 | 활용 목적 | 접근성 |
|---|---|---|---|---|---|
| **CWRU Bearing** | Case Western Reserve Univ. | 12 kHz / 48 kHz | 정상, 내륜·외륜·전동체 결함(0.007~0.021 in) | 정상/이상 2클래스 및 결함 유형 다중 클래스 분류 | 공개(무료), Zenodo/Kaggle 미러 존재 |
| **NASA IMS Bearing** | NASA PCoE / Univ. Cincinnati | 20 kHz | 베어링 파손까지의 전 수명(run-to-failure) 열화 데이터 3개 세트 | 열화 진행도(잔여수명 RUL) 및 열화 단계 분류 | 공개(무료), data.nasa.gov |
| **Paderborn (PU) Bearing** | Paderborn Univ. | 64 kHz | 인공·실제 손상 베어링 32종, 진동+전류 동시 측정 | 결함 유형 분류, 전류-진동 융합 | 공개(비상업적 CC BY-NC 4.0) |
| **XJTU-SY Run-to-Failure** | Xi'an Jiaotong Univ. | 25.6 kHz | 다양한 부하/속도 조건의 전 수명 열화 데이터 | 열화 단계 분류, RUL 예측 | 공개(무료) |
| **FEMTO (PRONOSTIA)** | FEMTO-ST | 25.6 kHz | 가속 수명 시험을 통한 열화 데이터 | RUL 예측 표준 | 공개(무료) |

### 2.2 데이터셋 선정 전략

- **정상/이상 2클래스 분류 + 결함 유형(내륜/외륜/전동체) 다중 클래스 분류**는 **CWRU** 데이터셋이 가장 적합하다. 논문 인용이 많아 비교 대상(관련 연구) 확보가 용이하고, 커뮤니티 지원이 풍부하다.
- **열화 단계 분류 및 시간에 따른 열화 추이(trend) 분석**은 **NASA IMS** 데이터셋이 적합하다. 초기(정상) ~ 파손(이상)까지의 시간적 변화를 관찰할 수 있어, 예지보전의 "예지" 특성을 강조하는 논문에 적합하다.
- **실제 산업 환경에서의 손상(실제 마모로 인한 손상)**을 포함하는 **Paderborn** 데이터셋은 실용성 검증에 적합하다.

> **제안** : 본 연구에서는 (1) **CWRU**로 2/4클래스 분류 모델을 주로 구축하고, (2) **NASA IMS**로 열화 단계 분류(또는 이상 점수 추이)를 추가 실험하며, (3) 여유가 되면 **Paderborn**으로 교차 검증(일반화 성능)을 수행하는 3단계 실험 설계를 제안한다.

```text
[실험 설계]
실험 1: CWRU 정상/이상 2클래스  → 4kHz 이하로 다운샘플링 → 1D-CNN
실험 2: CWRU 결함 유형 4클래스(정상/내륜/외륜/전동체) → 1D-CNN
실험 3: NASA IMS 열화 단계(정상/초기/중기/심화/파손) → 1D-CNN
실험 4: Paderborn 교차 검증(일반화 분석)
```

---

## 3. 시스템 아키텍처

### 3.1 전체 시스템 구성도

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                            PHASE A : PC (학습/검증)                     │
│                                                                          │
│  공개 진동 데이터셋                                                       │
│  (CWRU / NASA IMS / Paderborn)                                          │
│        │                                                                 │
│        ▼                                                                 │
│  [전처리] 다운샘플링 · 정규화 · 슬라이딩 윈도우 분할                         │
│        │                                                                 │
│        ▼                                                                 │
│  [특징 추출] (선택) 시간/주파수 영역 통계 특징                              │
│        │                                                                 │
│        ▼                                                                 │
│  [모델 학습] 1D-CNN / LSTM (TensorFlow/Keras)                           │
│        │                                                                 │
│        ▼                                                                 │
│  [변환] 양자화(int8) TFLite 변환                                         │
│        │                                                                 │
│        ▼                                                                 │
│  [PC 검증] 정확도 · Precision/Recall/F1 · 혼동행렬 분석                    │
└──────────────────────────────────────────────────────────────────────────┘
        │ (TFLite 모델 파일: model_int8.tflite)
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            PHASE B : MCU (배포/실시간)                  │
│                                                                          │
│  [STM32Cube.AI] 모델 분석 → 검증 → 최적화 → C 코드 생성                  │
│        │   Network + weights
│        ▼                                                                 │
│  NUCLEO-F411RE (Cortex-M4F)  또는  NUCLEO-H753ZI (Cortex-M7)            │
│        │                                                                 │
│   진동 센서(가속도계, 예: LIS3DSH/ISM330DHCX)  ← ADC/SPI/I2C            │
│        │                                                                 │
│        ▼                                                                 │
│   MCU 내 실시간 추론(정상/이상)                                           │
│        │                                                                 │
│        ▼                                                                 │
│   결과 출력: UART/터미널, LED, LCD, (옵션) 블루투스                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 흐름 요약

| 단계 | 위치 | 작업 | 산출물 |
|---|---|---|---|
| 1 | PC | 데이터 획득·전처리 | 전처리된 NumPy/TFRecord |
| 2 | PC | 특징 추출 | 특징 벡터 (선택) |
| 3 | PC | 모델 학습 | `model.keras` / `.h5` |
| 4 | PC | TFLite 변환·양자화 | `model_int8.tflite` |
| 5 | PC | 추론 검증 | 정확도/혼동행렬 보고서 |
| 6 | PC→MCU | STM32Cube.AI 코드 생성 | `network.c`, `network_data.c` |
| 7 | MCU | 실시간 추론 | 정상/이상 판별 출력 |

---

## 4. 실험 환경 구축

> **상세 설치 절차는 [docs/03_setup.md](docs/03_setup.md)에 기술되어 있다.**

### 4.1 PC(학습) 환경 — 권장 사양

| 항목 | 권장 사양 |
|---|---|
| OS | Windows 10/11 (64-bit) 또는 Ubuntu 20.04+ |
| CPU | Intel i5 / AMD Ryzen 5 이상 |
| GPU (선택) | NVIDIA CUDA 지원 GPU (RTX 30/40 시리즈) |
| RAM | 16 GB 이상 |
| Python | 3.10 ~ 3.12 |
| 저장소 | 20 GB 이상 (데이터셋 포함) |

### 4.2 사용 소프트웨어 스택

| 도구 | 용도 |
|---|---|
| **Python 3.10+** | 전체 파이프라인 |
| **Anaconda / Miniconda** | 가상환경 관리 |
| **Jupyter Notebook / VS Code** | 코드 작성·실행 |
| **TensorFlow 2.15+** | 딥러닝 모델 학습·변환 |
| **TFLite Interpreter** | PC 추론 검증 |
| **NumPy, pandas, SciPy** | 데이터 처리·통계 |
| **matplotlib, seaborn** | 시각화 |
| **scikit-learn** | 평가 지표 계산, 분할 |
| **scipy** | 신호 처리(다운샘플링, FFT) |
| **STM32CubeMX** | MCU 초기화·주변장치 설정 및 X-CUBE-AI 연동 |
| **STM32CubeIDE** | 펌웨어 빌드·디버깅 |
| **X-CUBE-AI (STM32Cube.AI) / STM32Cube AI Studio** | 모델 → C 코드 생성 |
| **STM32CubeProgrammer** | 바이너리 플래싱 |

### 4.3 가상환경 생성 예시(Python)

```powershell
# Miniconda 가정
conda create -n vibai python=3.11 -y
conda activate vibai

pip install tensorflow==2.15.0
pip install numpy pandas scipy scikit-learn matplotlib seaborn
pip install ipykernel jupyter

# CUDA GPU 사용 시 (선택)
# conda install -c nvidia cudatoolkit=11.8
```

---

## 5. 데이터 획득 및 전처리

> **실행 가능한 예제: [code/01_data_preprocessing](code/01_data_preprocessing)**

### 5.1 데이터 획득

각 데이터셋의 상세 다운로드 방법은 [docs/02_datasets.md](docs/02_datasets.md)에 정리되어 있다.

```text
data/
├── cwru/            # CWRU .mat 파일 (다운샘플 48kHz 등)
│   ├── Normal/
│   ├── IR_007/      # 내륜 결함 0.007in
│   ├── OR_007/      # 외륜 결함
│   └── B_007/       # 전동체(볼) 결함
├── nasa_ims/        # NASA IMS raw 데이터 (첫번째 시험 세트 권장)
└── paderborn/       # Paderborn .mat 파일
```

### 5.2 전처리 파이프라인

1. **로딩**: `.mat`(MATLAB) 또는 `txt` 파일을 읽어 진동 신호를 1D 배열로 변환
2. **다운샘플링** (선택): MCU의 저비용·저전력 특성을 고려해 4kHz 또는 2kHz로 다운샘플링 — 메모리·연산량 절감, 모델 경량화에 기여. 단, 나이퀴스트(Nyquist) 조건(결함 특성 주파수 < Fs/2)을 만족해야 함
3. **정규화(Normalization)**: 평균 0, 표준편차 1로 표준화(z-score) 또는 min-max 정규화
4. **윈도우 분할(Sliding Window)**: 긴 신호를 고정 길이(예: 1024, 2048 샘플) 윈도우로 분할
   - 윈도우 길이는 논문에서 하이퍼파라미터로 실험 (예: 256/512/1024/2048)
   - 겹침(overlap/strid)은 0% 또는 50%로 설정
5. **라벨링**: 각 윈도우에 정상/이상(및 결함 유형) 라벨 부여
6. **데이터 분할**: 하이퍼파라미터로 실험 (예: 256/512/1024/2048) → **Train / Validation / Test** 분할

> **중요(데이터 누수 방지)**: 동일한 물리적 실험(같은 베어링, 같은 신호 파일)의 세그먼트가 train/test 양쪽에 섞이면 데이터 누수(data leakage)로 인해 성능이 과대평가된다. **반드시 파일(실험) 단위로 분할**해야 한다. (Hendriks et al., 2022 지적)

```python
# 전처리 예시 (골격)
def preprocess(raw_signal, fs_source=48000, fs_target=4000, window=1024):
    # 1) 다운샘플링 (디시메이션)
    from scipy.signal import decimate  # 안티앨리어싱 필터 내장
    ds = decimate(raw_signal, int(fs_source/fs_target))
    # 2) 정규화 (z-score)
    ds = (ds - ds.mean()) / ds.std()
    # 3) 윈도우 분할
    n = len(ds) // window
    frames = ds[:n*window].reshape(-1, window)
    return frames
```

---

## 6. 특징 추출 및 데이터셋 구성

> **실행 가능한 예제: [code/01_data_preprocessing/extract_features.py](code/01_data_preprocessing/extract_features.py)**

딥러닝 모델은 원시(시간 영역) 파형을 직접 입력으로 사용할 수 있으나, 전통적 머신러닝 기반 비교 실험 및 논문의 근거 자료를 위해 **시간 영역·주파수 영역 통계 특징**도 함께 추출한다.

### 6.1 시간 영역 특징 (Time-domain Features)

- 평균(Mean), RMS (Root Mean Square)
- 표준편차(Std), 분산(Variance)
- 첨도(Kurtosis), 왜도(Skewness)
- 피크값(Peak), 피크-피크(Peak-to-Peak)
- 파고율(Crest Factor) = Peak / RMS
- 임펄스 팩터(Impulse Factor), 여유율(Clearance Factor)

### 6.2 주파수 영역 특징 (Frequency-domain Features)

- FFT 기반 스펙트럼
- 주요 주파수 피크 및 진폭
- 중심 주파수, RMS 주파수, 주파수 표준편차
- 특정 결함 주파수(BPFI/BPFO/BSF/FTF) 대역 에너지 (베어링 특성 주파수)

### 6.3 데이터셋 구성 요약

```text
데이터셋  X¯  (N, window_length)   : 입력 시계열 윈도우
라벨     y   (N, num_classes)      : 원-핫 인코딩
분할     Train 70% / Val 15% / Test 15%   (실험 단위 스플릿)
```

| 클래스 라벨 | 의미 |
|---|---|
| 0 | 정상(Normal) |
| 1 | 내륜 결함(IR) |
| 2 | 외륜 결함(OR) |
| 3 | 전동체 결함(Ball) |

---

## 7. 딥러닝 모델 설계 및 학습 (PC)

> **실행 가능한 예제: [code/02_training/train_1dcnn.py](code/02_training/train_1dcnn.py)**

### 7.1 모델 아키텍처: 1D-CNN

진동 시계열에 가장 널리 쓰이는 구조 중 하나로 1D-CNN이며, 학습 파라미터가 적고 TFLite/MCU 변환에 매우 친화적이다.

```text
입력: (window_length, 1)  예: (1024, 1)
  │
  ▼
Conv1D (32 filters, kernel=32, ReLU) + MaxPooling1D(4)
  │
  ▼
Conv1D (64 filters, kernel=16, ReLU) + MaxPooling1D(4)
  │
  ▼
Conv1D (128 filters, kernel=8, ReLU) + GlobalAveragePooling1D
  │
  ▼
Dense (64, ReLU) + Dropout(0.5)
  │
  ▼
Dense (num_classes, Softmax)
```

```python
# 골격 코드
def build_1dcnn(window_len, num_classes):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(window_len, 1)),
        tf.keras.layers.Conv1D(32, 32, activation='relu'),
        tf.keras.layers.MaxPooling1D(4),
        tf.keras.layers.Conv1D(64, 16, activation='relu'),
        tf.keras.layers.MaxPooling1D(4),
        tf.keras.layers.Conv1D(128, 8, activation='relu'),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    return model
```

### 7.2 학습 설정

| 하이퍼파라미터 | 값 |
|---|---|
| 손실 함수 | CategoricalCrossentropy |
| 옵티마이저 | Adam (lr=1e-3) |
| 배치 크기 | 128 |
| 에폭 수 | 50 (조기 종료 patience=10) |
| 콜백 | EarlyStopping, ModelCheckpoint, ReduceLROnPlateau |
| 학습률 스케줄 | 처음 1e-3, 검증 손실 정체 시 0.5배 감소 |

### 7.3 평가 지표

- **Accuracy (정확도)**
- **Precision (정밀도)**, **Recall (재현율)**, **F1-score**
- **Confusion Matrix (혼동행렬)**
- **ROC-AUC** (2클래스, 선택)

> 이상 탐지에서는 정상→이상 오탐(false positive)과 이상 누락(false negative)의 비용이 다르므로, 단순 정확도 외에 **Precision/Recall/F1**을 함께 보고해야 한다.

---

## 8. 모델 변환 및 양자화 (TFLite)

> **실행 가능한 예제: [code/02_training/convert_tflite.py](code/02_training/convert_tflite.py)** 및 **STM32Cube.AI int8 지원**

### 8.1 배경

MCU의 Flash는 일반적으로 수백 KB~수MB이며 RAM은 수십~수백 KB로 극히 제한된다. FP32 모델을 그대로 배포하면 용량을 초과하므로 **정수(int8) 양자화(Quantization)**가 필수적이다. int8 양자화는 모델 크기를 1/4로 줄이고, 연산 속도를 높이며, 전력 소모를 낮춘다.

### 8.2 양자화 종류

| 방식 | 설명 | 권장 |
|---|---|---|
| 사후 정적 양자화(PTQ, int8) | 학습 후 대표 데이터셋으로 가중치·활성화를 int8로 변환 | **권장 (간단, 충분히 정확)** |
| 양자화 인지 학습(QAT) | 양자화 오차를 학습 중 반영 | 정확도 저하가 클 때 적용 |

### 8.3 변환 예시

```python
import tensorflow as tf
import numpy as np

model = tf.keras.models.load_model('saved_model/model.keras')

def representative_dataset():
    # 대표 데이터셋: int8 양자화 스케일 결정을 위한 소표본
    for i in range(0, len(X_calib), 32):
        yield [X_calib[i:i+32].astype(np.float32)]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8     # MCU 친화적
converter.inference_output_type = tf.int8

tflite_model = converter.convert()
with open('tflite_models/model_int8.tflite', 'wb') as f:
    f.write(tflite_model)
print('Saved int8 quantized TFLite model')
```

> STM32Cube.AI는 int8 TFLite 모델을 직접 읽어 MCU 최적화 C 코드로 변환한다. FP32(`.tflite`)도 지원하나 메모리·속도 측면에서 int8 배포를 권장한다.

---

## 9. PC에서의 추론 검증

> **실행 가능한 예제: [code/03_pc_inference/pc_inference.py](code/03_pc_inference/pc_inference.py)**

MCU 배포 **이전에** PC에서 TFLite 모델로 추론 검증을 수행하여, 양자화 전후 정확도를 비교한다.

### 9.1 검증 절차

1. TFLite Interpreter 로드
2. 입력 텐서를 int8 양자화 파라미터(scale, zero_point)로 양자화
3. 추론 수행
4. 출력 텐서를 역양자화
5. 정상/이상(및 결함 유형) 예측 및 평가 지표 계산

```python
import tensorflow as tf

interpreter = tf.lite.Interpreter(model_path='tflite_models/model_int8.tflite')
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# 입력 양자화 파라미터
in_scale, in_zp = input_details[0]['quantization']
out_scale, out_zp = output_details[0]['quantization']

def infer(sample_float32):
    q = sample_float32 / in_scale + in_zp
    q = q.astype(np.int8)
    interpreter.set_tensor(input_details[0]['index'], q.reshape(input_shape))
    interpreter.invoke()
    out_q = interpreter.get_tensor(output_details[0]['index'])
    out_float = (out_q.astype(np.float32) - out_zp) * out_scale
    return out_float
```

### 9.2 보고 항목

- 양자화 전(FP32) vs 후(int8) 정확도 비교 표
- Precision / Recall / F1 (클래스별 + 매크로)
- 혼동행렬 시각화
- 클래스별 오분류 사례 분석

---

## 10. STM32Cube.AI 기반 MCU 배포

> **상세 가이드: [docs/04_stm32_cubeai_deploy.md](docs/04_stm32_cubeai_deploy.md)**

### 10.1 타겟 MCU 비교

| 항목 | NUCLEO-F411RE | NUCLEO-H753ZI |
|---|---|---|
| 코어 | Cortex-M4F (FPU) | Cortex-M7 (FPU, L1 캐시) |
| 클럭 | 100 MHz | 480 MHz |
| Flash | 512 KB | 2 MB |
| SRAM | 128 KB | 512 KB (+TCM) |
| AI 수행 | **소프트웨어 추론** (저비용) | 소프트웨어 추론, 더 큰 모델 가능 |
| 특징 | 입문·저비용, 신호 획득+추론 | 고성능, 복잡 모델·더 높은 실시간성 |

- **제안**: 먼저 **NUCLEO-F411RE**로 기본 검증(경량 1D-CNN int8)을 수행하고, 모델이 커지거나 더 높은 성능이 필요하면 **NUCLEO-H753ZI**로 확장. 두 보드 모두 STM32Cube.AI가 지원한다.

### 10.2 흐름 (STM32Cube.AI)

```text
①STM32CubeIDE 프로젝트 생성 (보드 선택)
        │
        ▼
② [Middleware] X-CUBE-AI 활성화 → Add Network
        │        model_int8.tflite 로딩
        ▼
③ Analyze (성능·메모리 리포트)
        ▼
④ Validate on target (보드에서 입력/출력 검증, 선택)
        ▼
⑤ Generate Code → network.c, network_data.c, network.h  생성
        ▼
⑥ Application 코드 작성: 신호 획득 → 전처리 → ai_run() 추론 → 결과
        ▼
⑦ Build & Flash (STM32CubeIDE / STM32CubeProgrammer)
        ▼
⑧ 실시간 추론 확인 (터미널/LED)
```

### 10.3 MCU 응용 코드 골격

```c
#include "app_x-cube-ai.h"
#include "network.h"
#include "network_data.h"

void app_entry(void) {
    ai_float input[AI_NETWORK_IN_1_SIZE];
    ai_float output[AI_NETWORK_OUT_1_SIZE];

    ai_network_params params = {
        .network_data = const_cast<ai_handle_t*>(network_data_weights_get(),
                                                 AI_NETWORK_DATA_WEIGHTS_SIZE),
    };
    ai_network_init(&params);

    while (1) {
        read_vibration_frame(input);      // ADC/SPI 액셀로 진동 윈도우 획득
        normalize(input, 1, 2);           // 전처리 (필요 시)
        ai_run(&params, input, output);   // 추론
        int cls = argmax(output);         // 정상/이상 판별
        set_led(cls);
        uart_send_printf("Class=%d conf=%.2f\r\n", cls, output[cls]);
        HAL_Delay(10);
    }
}
```

---

## 11. 실시간 추론 및 결과 해석

### 11.1 성능 측정 항목

| 항목 | 측정 방법 | 목표 |
|---|---|---|
| 추론 시간 | `HAL_GetTick()` / SysTick 타이머 또는 DWT 사이클 카운터 | 실시간(FPS) 확보 |
| Flash 사용량 | 빌드 리포트 또는 STM32CubeProgrammer | 모델 + 펌웨어가 Flash 이내 |
| RAM 사용량 | 빌드 리포트 / 작업 중량 | SRAM 이내 |
| 정확도 | 실제 보드 추론 vs 라벨 비교 | PC 대비 허용 가능한 저하 |
| 전력 소모 | 전원 공급기/전류계 | 저전력 특성 확인 |

### 11.2 결과 분석 및 시각화

- **PC(int8) vs MCU 추론 결과 비교 산점도/일치율**
- 클래스 예측 정확도 요약 표
- 실시간 FPS(초당 추론 횟수) 측정
- 에너지 효율(FPS/W) 계산

---

## 12. 논문 작성 가이드

> 자세한 틀은 [docs/05_thesis_guide.md](docs/05_thesis_guide.md)를 참고하라. 석사학위 논문(또는 학회 논문)의 표준 구조를 제공한다.

### 12.1 논문 구조 제안 (한국어)

| 장 | 제목 | 내용 |
|---|---|---|
| 국문초록 / Abstract | 연구 요약 | 목적·방법·주요 결과·결론 |
| 제1장 | 서론 | 연구 배경, 목적, 범위, 구성 |
| 제2장 | 관련 연구 | 예지보전, 진동 분석, 딥러닝 기반 결함 진단, MCU 엣지 AI |
| 제3장 | 실험 설계 및 방법 | 데이터셋, 전처리, 모델, 평가 지표 |
| 제4장 | PC 기반 모델 학습 결과 | 실험 결과, 정확도 비교 |
| 제5장 | MCU 기반 구현 및 검증 | STM32Cube.AI 배포, 실시간 추론, 성능 |
| 제6장 | 결론 | 요약, 기여, 한계, 향후 연구 |
| 참고문헌 | References | (아래 참고문헌 장 활용) |

### 12.2 실험 결과 보고 예시 (표 템플릿)

**표 X. 데이터셋별 모델 성능 (Accuracy / Macro-F1)**

| 데이터셋 | Model | 클래스 수 | FP32 Acc | int8 Acc | F1 |
|---|---|---|---|---|---|
| CWRU | 1D-CNN | 2 | 99.8% | 99.5% | 0.995 |
| CWRU | 1D-CNN | 4 | 99.5% | 99.1% | 0.991 |
| NASA IMS | 1D-CNN | 5(열화단계) | 95.2% | 94.0% | 0.938 |
| Paderborn | 1D-CNN | 3 | 97.1% | 96.3% | 0.960 |

*(실제 값은 학습 후 채워 넣을 것)*

**표 X. NUCLEO 보드별 메모리 및 추론 성능**

| 보드 | Flash 사용량 | RAM 사용량 | 추론 시간 | FPS |
|---|---|---|---|---|
| NUCLEO-F411RE | ~XXX KB | ~XX KB | ~X ms | ~XX |
| NUCLEO-H753ZI | ~XXX KB | ~XX KB | ~X ms | ~XXX |

---

## 13. 참고문헌

아래는 본 연구에서 직접 사용하고 인용할 주요 문헌 목록이다. (BibTeX 형식은 [docs/05_thesis_guide.md](docs/05_thesis_guide.md)에 수록)

### 데이터셋 원문

1. **CWRU**: Case Western Reserve University Bearing Data Center. https://engineering.case.edu/bearingdatacenter
2. **NASA IMS**: Lee, J., Qiu, H., Yu, G., Lin, J., & Rexnord Technical Services (2007). *Bearing Data Set*. NASA Prognostics Data Repository, NASA Ames Research Center. https://data.nasa.gov/dataset/IMS-Bearings
3. **Paderborn**: Lessmeier, C., Kimotho, J. K., Zimmer, D., & Sextro, W. (2016). *Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: a Benchamrk Data Set for Data-Driven Classification*. PHM Society European Conference.
4. **XJTU-SY**: Wang, B., Lei, Y., Li, N., & Li, N. (2020). A hybrid prognostics approach for estimating remaining useful life of rolling element bearings. *IEEE Trans. Reliability*.

### 딥러닝 · 예지보전 · 엣지AI 관련

5. Hendriks, J., Dumond, P., & Fowlie, D. (2022). A critical analysis of the CWRU bearing fault dataset for benchmarking. *IEEE Sensors Journal*.
6. STMicroelectronics. *STM32Cube.AI (X-CUBE-AI) User Manual* (UM2526).
7. David, R., et al. (2021). *TensorFlow Lite Micro: Embedded Machine Learning for TinyML Systems*. Proceedings of MLSys.
8. Warden, P., & Situnayake, D. (2019). *TinyML: Machine Learning with TensorFlow Lite*. O'Reilly Media.

---

## 부록: 프로젝트 디렉터리 구조

```text
C:\VibrationPMA\
├── README.md                          ← 본 문서 (마스터)
├── docs\
│   ├── 01_overview.md                 ← 개요 (본 README와 중복, 논문용 별도)
│   ├── 02_datasets.md                 ← 데이터셋 상세 조사
│   ├── 03_setup.md                    ← 환경 구축 상세
│   ├── 04_stm32_cubeai_deploy.md      ← MCU 배포 상세
│   ├── 05_thesis_guide.md             ← 논문 작성 가이드·표·BibTeX
│   └── 06_results_template.md         ← 결과 보고서 양식
├── code\
│   ├── 01_data_preprocessing\
│   │   ├── 01_load_cwru.py
│   │   ├── 02_preprocess.py
│   │   └── extract_features.py
│   ├── 02_training\
│   │   ├── train_1dcnn.py
│   │   ├── convert_tflite.py
│   │   └── evaluate.py
│   ├── 03_pc_inference\
│   │   └── pc_inference.py
│   └── 04_stm32_cubeai\
│       └── (STM32CubeIDE 프로젝트 안내)
└── data\  (사용자 다운로드)  /  models\  /  results\  (생성물)
```

---

*본 문서는 교육·연구 목적으로 작성되었으며, 모든 데이터셋은 각 원저작자의 라이선스(특히 Paderborn의 CC BY-NC 4.0)를 준수하여 학술적 용도로만 사용해야 한다.*
