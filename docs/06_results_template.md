# 결과 보고서 양식

다음 실험을 모두 수행한 뒤 이 양식에 결과를 채워 넣어 논문 근거 자료를 만든다.

## 1. PC 실험 결과

### 데이터셋별 성능
| 실험 | 데이터셋 | 클래스 | Window | 옵티마이저 | Epochs | FP32 Acc | int8 Acc | Macro-F1 | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CWRU | 2 | 1024 | Adam | 50 |  |  |  |  |
| 2 | CWRU | 4 | 1024 | Adam | 50 |  |  |  |  |
| 3 | NASA IMS | 5 | 1024 | Adam | 50 |  |  |  |  |
| 4 | Paderborn | 3 | 1024 | Adam | 50 |  |  |  |  |

### 혼동행렬 (저장 위치: results/cm_*.png)

### 학습 곡선 (results/training_curves.png)

## 2. 양자화 정보

| 모델 | 입력형식 | 출력형식 | 크기(Byte) | 압축비 |
|---|---|---|---|---|
| model_fp32.tflite | FP32 | FP32 |  | 1x |
| model_int8.tflite | int8 | int8 |  | ~1/4 |

사용한 대표 데이터셋 수: ____ 샘플

## 3. PC 추론 검증

- PC int8 정확도: ____ %
- PC FP32 정확도: ____ %
- 정확도 저하: ____ % (허용 수준: 보통 <1%)

## 4. MCU 구현 결과

| 보드 | Flash(KB) | RAM(KB) | 추론시간(ms) | FPS | Test Acc(%) | 전력(mW) | AI 콘솔 결과 |
|---|---|---|---|---|---|---|---|
| NUCLEO-F411RE |  |  |  |  |  |  |  |
| NUCLEO-H753ZI |  |  |  |  |  |  |  |

### PC vs MCU 결과 일치율
- 일치(same class) 비율: ____ %
- 불일치 지점 분석:

## 5. 기록 일자 및 환경

- 실험일: ____
- Python/TF 버전: ____
- STM32CubeIDE 버전: ____
- X-CUBE-AI 버전: ____
- random seed: 42
