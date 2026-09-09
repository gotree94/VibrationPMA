# 논문(석사학위) 작성 가이드

본 문서는 "진동 신호 기반 예지보전 시스템의 MCU 엣지 AI 구현" 연구를 **석사학위 논문**(또는 학회 논문) 형식으로 작성하기 위한 뼈대를 제공한다.

---

## 1. 논문 제목 제안

- 「회전기계 진동 신호 기반 예지보전을 위한 경량 딥러닝 모델과 STM32 MCU 엣지 AI 구현」
- 「Vibration-based Predictive Maintenance using Lightweight Deep Learning on STM32 MCU Edge AI」
- 「진동 시계열 데이터의 엣지 추론을 위한 1D-CNN 모델 경량화와 MCU 배포」

---

## 2. 논문 구조 (한국어 석사 논문 표준)

```
[표지 / 국문초록 / Abstract]
[목차 / 표목차 / 그림목차]

1. 서론
   1.1 연구 배경 및 필요성
   1.2 연구 목적 및 범위
   1.3 논문 구성

2. 관련 연구
   2.1 예지보전의 개념과 필요성
   2.2 진동 신호 기반 기계상태 진단
   2.3 딥러닝 기반 결함 분류 (1D-CNN, LSTM 등)
   2.4 엣지 AI / TinyML과 MCU 추론
   2.5 공개 데이터셋 (CWRU, NASA IMS, Paderborn)

3. 실험 설계 및 방법
   3.1 시스템 전체 구조
   3.2 데이터셋 및 전처리
   3.3 특징 추출 (선택)
   3.4 모델 설계 (1D-CNN)
   3.5 TFLite 변환 및 양자화
   3.6 평가 지표
   3.7 MCU 배포 방법 (STM32Cube.AI)

4. PC 기반 모델 학습 및 검증 결과
   4.1 실험 환경
   4.2 데이터셋별 학습 결과
   4.3 FP32 vs int8 정확도 비교
   4.4 오분류 분석

5. MCU 기반 구현 및 실시간 검증
   5.1 타겟 보드 및 설정 (F411RE / H753ZI)
   5.2 STM32Cube.AI 코드 생성 결과
   5.3 메모리 및 추론 성능 분석
   5.4 실시간 추론 정확도
   5.5 전력 소모 분석

6. 결론
   6.1 연구 요약
   6.2 기여점
   6.3 한계점
   6.4 향후 연구

[참고문헌]
[부록]
```

---

## 3. 필수 실험 결과 표 (템플릿)

### 표 A. 데이터셋별 int8 모델 성능

| 데이터셋 | 클래스 수 | Window | FP32 Acc | int8 Acc | Macro-F1 |
|---|---|---|---|---|---|
| CWRU | 2 | 1024 |  |  |  |
| CWRU | 4 | 1024 |  |  |  |
| NASA IMS | 5 | 1024 |  |  |  |
| Paderborn | 3 | 1024 |  |  |  |

### 표 B. MCU 배포 결과

| 보드 | Flash(KB) | RAM(KB) | 추론시간(ms) | FPS | 정확도(%) | 전력(mW) |
|---|---|---|---|---|---|---|
| NUCLEO-F411RE |  |  |  |  |  |  |
| NUCLEO-H753ZI |  |  |  |  |  |  |

### 그림 목록 (제안)
1. 시스템 전체 구조도
2. 데이터셋 파형 예시 (정상/내륜/외륜/전동체)
3. FFT 스펙트럼 비교
4. 모델 아키텍처 도식
5. 학습 손실/정확도 곡선
6. 혼동행렬
7. int8 양자화 전후 정확도 비교 막대그래프
8. MCU 배포 모식도 (STM32Cube.AI 파이프라인)
9. 실시간 추론 결과 파형/시간축
10. F411 vs H753 성능/전력 비교

---

## 4. 실험 방법론 수립 시 반드시 지킬 것

1. **데이터 누수 방지**: 파일(실험) 단위 분할. Hendriks et al.(2022)의 지적 참조.
2. **클래스 불균형**: 이상 샘플이 정상보다 많은 CWRU 특성상, 평가 시 가중 지표(weighted/macro)와 Precision-Recall 확인.
3. **재현성**: `random_seed` 고정, 환경 버전 기록(requirements.txt).
4. **신뢰성**: 동일 모델을 최소 5회 반복 실행 → 평균±표준편차 보고.
5. **공정 비교**: PC 모델과 MCU 모델이 **동일 입력·동일 양자화 파라미터**로 비교되어야 함.

---

## 5. 참고문헌 BibTeX

```bibtex
% 데이터셋
@misc{CWRU_data,
  title = {{Case Western Reserve University} Bearing Data Center},
  url   = {https://engineering.case.edu/bearingdatacenter},
  note  = {Accessed: 2025}
}

@misc{NASA_IMS,
  author = {Lee, Jay and Qiu, Hai and Yu, Gang and Lin, Jing and {Rexnord Technical Services}},
  title  = {{Bearing Data Set, NASA Prognostics Data Repository}},
  year   = {2007},
  url    = {https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/}
}

@inproceedings{Lessmeier2016,
  author    = {Lessmeier, Christian and Kimotho, James Kuria and Zimmer, Detmar and Sextro, Walter},
  title     = {{Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification}},
  booktitle = {Proceedings of the European Conference of the PHM Society},
  year      = {2016}
}

% 데이터 누수 관련
@article{Hendriks2022,
  author  = {Hendriks, Jason and Dumond, Patrick and Fowlie, David},
  title   = {{A Critical Analysis of the CWRU Bearing Fault Dataset for Benchmarking}},
  journal = {IEEE Sensors Journal},
  year    = {2022}
}

% 엣지 AI / TFLM
@inproceedings{David2021,
  author    = {David, Robert and others},
  title     = {{TensorFlow Lite Micro: Embedded Machine Learning for TinyML Systems}},
  booktitle = {Proceedings of MLSys},
  year      = {2021}
}

@book{Warden2019,
  author    = {Warden, Pete and Situnayake, Daniel},
  title     = {{TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers}},
  publisher = {O'Reilly Media},
  year      = {2019}
}

% ST
@misc{STM32CubeAI,
  title = {{STM32Cube.AI (X-CUBE-AI) — AI model optimizer for STM32}},
  url   = {https://www.st.com/en/embedded-software/x-cube-ai.html},
  note  = {Accessed: 2025}
}
```

---

## 6. 심사/게재 시 자주 받는 질문 대비

1. **"왜 1D-CNN인가?"** → 파라미터 수 적음, 시계열 지역 패턴 포착, MCU 변환 용이. LSTM 대비 경량.
2. **"윈도우 길이는 어떻게 정했나?"** → 결함 특성 주파수를 포함하는 최소 길이 + 실험(256/512/1024/2048) 비교.
3. **"양자화 정확도 저하는 어느 정도인가?"** → FP32 vs int8 표로 정량 제시.
4. **"실제 MCU 성능은?"** → 추론시간, FPS, 메모리, 전력 표로 정량 제시.
5. **"일반화는?"** → 서로 다른 데이터셋(CWRU→Paderborn) 교차 실험. 다만 도메인 차이가 크므로 pretraining/스트레스 서술.

---

## 7. 석사논문 심사 체크리스트

- [ ] 연구 문제 정의가 명확한가
- [ ] 관련 연구와의 차별점(MCU 배포 엔드투엔드, 경량화, 실시간성)이 드러나는가
- [ ] 데이터셋 출처와 라이선스 명시
- [ ] 실험 설계가 공정·재현 가능한가
- [ ] 평가 지표가 적절한가 (정확도 + F1)
- [ ] PC vs MCU 성능 비교 포함
- [ ] 한계점과 향후 연구가 명시되어 있는가
