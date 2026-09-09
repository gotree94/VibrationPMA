# 데이터셋 상세 조사 (진동 · 베어링 예지보전)

이 문서는 진동(시계열) 데이터를 이용한 예지보전 연구에 사용할 수 있는 **신뢰성 있는 공개 데이터셋**을 정리한다. 본 프로젝트의 마스터 문서 `README.md`의 [제2장](README.md#2-데이터셋-조사-및-선정)에 대한 상세 버전이다.

---

## 표: 데이터셋 요약 비교

| 데이터셋 | 제공기관 | 샘플링률 | 채널 | 손상 종류 | 라벨 | 용도 | 접근성/라이선스 | 다운로드 |
|---|---|---|---|---|---|---|---|---|
| **CWRU** | Case Western Reserve Univ. (미국) | 12 kHz / 48 kHz | 진동(가속도) | 정상 / 내륜(IR) / 외륜(OR) / 전동체(B), 0.007~0.021 in | 2~4클래스 가능 | 결함 유형 분류 | 무료·공개 | [공식](https://engineering.case.edu/bearingdatacenter/download-data-file) · [Zenodo(mirror)](https://zenodo.org/records/10987113) · [Kaggle](https://www.kaggle.com/datasets/brjapon/cwru-bearing-datasets) |
| **NASA IMS** | NASA PCoE / Univ. Cincinnati (미국) | 20 kHz | 진동(가속도, 8채널) | run-to-failure 열화 (파손까지) | 시간 경과 인덱스 | 열화 단계 분류, RUL, 이상 점수 추이 | 무료·공개 | [data.nasa.gov IMS](https://data.nasa.gov/dataset/ims-bearings) · [NASA PCoE](https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip) |
| **Paderborn(PU)** | Paderborn Univ. (독일) | 64 kHz | 진동+모터 전류(2ch) | 인공 손상(12) / 실제 손상(14) / 정상(6) | 3클래스 이상 | 결함 유형 분류, 전류-진동 융합 | 공개 · **CC BY-NC 4.0 (비상업)** | [공식](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download) |
| **XJTU-SY** | Xi'an Jiaotong Univ. (중국) | 25.6 kHz | 진동 | run-to-failure, 다양한 운전조건 | 시간 경과 인덱스 | RUL, 열화 단계 | 공개 | [GitHub](https://github.com/wang-bingshuai/...) 등 |
| **FEMTO(PRONOSTIA)** | FEMTO-ST (프랑스) | 25.6 kHz | 진동 | 가속 수명 시험 열화 | 시간 경과 인덱스 | RUL(표준 벤치마크) | 무료(등록) | [IEEE PHM Challenge](https://www.femto-st.fr/) |

---

## 1. CWRU 데이터셋 (가장 권장 · 표준 벤치마크)

### 1.1 개요
미국 Case Western Reserve University의 Bearing Data Center에서 제공하는 베어링 결함 진단 **표준 데이터셋**이다. 회전기계(2HP 모터)에 **EDM(전기방전가공)으로 가공한 단일점 결함**을 낸 베어링과 정상 베어링의 진동신호를 측정했다.

### 1.2 구조
- 부하 조건: 0 / 1 / 2 / 3 HP (→ 모터 속도 약 1797 / 1772 / 1750 / 1730 RPM)
- 결함 위치: 내륜(IR), 외륜(OR), 전동체(Ball, B)
- 결함 직경: 0.007 / 0.014 / 0.021 inch
- 측정 위치: Drive End(DE), Fan End(FE), Basement
- 샘플링률: 12 kHz(고장 48kHz도 존재)
- 파일 형식: `.mat` (MATLAB)

### 1.3 실험 설계 예시 (권장)
- **실험 1: 정상/이상 2클래스** → `Normal` vs (모든 결함)
- **실험 2: 결함 유형 4클래스** → `Normal / IR / OR / Ball` (특정 부하, 특정 결함 직경)
- **실험 3: 결함 크기 구분(선택)** → 0.007 / 0.014 / 0.021 in 분류 (난이도 있음, 논문에서 "분류 가능 여부" 논의 가능)

### 1.4 중요 주의 (데이터 누수)
- 동일 베어링이 서로 다른 부하(실험)에서 재사용되므로, **같은 베어링(파일)의 세그먼트가 train/test에 섞이지 않도록 반드시 파일 단위로 분할**해야 한다. (Hendriks et al., 2022)
- 논문 작성 시 본 연구의 분할 방식을 명확히 기술하는 것이 평가에 유리하다.

### 1.5 인용
```bibtex
@misc{CWRU_data,
  title = {{Case Western Reserve University} Bearing Data Center},
  url  = {https://engineering.case.edu/bearingdatacenter},
  note = {Accessed: 2025}
}
```

---

## 2. NASA IMS 데이터셋 (열화 · 예지특성 강조)

### 2.1 개요
미국 NASA의 Prognostics Center of Excellence(PCoE)에서 관리하며, Cincinnati 대학의 IMS(Intelligent Maintenance Systems)에서 수집한 **베어링 파손까지의 전 수명(run-to-failure)** 데이터이다.

### 2.2 구조
- 4개 베어링을 축에 장착, 2000RPM 상시 회전
- 샘플링률 20 kHz, 8채널 가속도계
- 총 3개 시험 세트 (첫 번째 세트의 베어링 1·2가 종말에 결함 발생 — 실험 3/4장에서 가장 많이 사용됨)
- 10분 간격으로 데이터 저장 → **시간이 지날수록 결함이 심화되는 "열화 추이"** 관찰 가능

### 2.3 실험 설계 예시
- **열화 단계 분류**: 시간 경과를 기준으로 5단계(정상→파손)로 구간화 후 다중 클래스 분류
- **이상 점수 추이**: 초기 정상 데이터만으로 학습한 모델(또는 재구성오차 기반 이상탐지)로 시간에 따른 이상 점수 곡선을 그리고, 파손 시점 전의 급격한 상승(경보 시점)을 확인 → **"예지"적 특성 강조**

### 2.4 인용
```bibtex
@misc{NASA_IMS,
  author = {Lee, Jay and Qiu, Hai and Yu, Gang and Lin, Jing and {Rexnord Technical Services}},
  title  = {{Bearing Data Set, NASA Prognostics Data Repository}},
  year   = {2007},
  url    = {https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/}
}
```

---

## 3. Paderborn(PU) 데이터셋 (실제 산업 손상 · 전류-진동 융합)

### 3.1 개요
독일 Paderborn 대학 KAt(설계·구동기술) 연구실에서 제공하는 베어링 데이터셋으로, **실제 마모(가속수명시험)로 인한 손상**을 포함하여 실용성이 높다. 진동 신호와 **모터 전류 신호**를 동시에 측정했다.

### 3.2 구조
- 베어링: 6203 타입
- 정상 6개 / 인공 손상 12개 / 실제 손상(가속수명시험) 14개
- 4가지 운전 조건, 각 조건당 4초 측정 20회 (`N15_M07_F10_KA01_1.mat` 형식)
- 샘플링률 64 kHz, 진동 1채널 + 전류 2채널, 속도·토크·하중·온도 지원

### 3.3 라이선스 주의
**CC BY-NC 4.0 (비상업적 이용만 허용)** — 학술 연구(석사논문)에는 사용 가능하나 상업적 이용 및 재배포가 제한된다. 인용 필수.

### 3.4 활용
- 결함 유형(정상/내륜/외륜) 분류의 **교차 데이터셋**으로 활용해 일반화 성능 검증
- 전류 신호와 진동 신호를 함께 사용하는 **멀티모달(융합) 실험** 가능

### 3.5 인용
```bibtex
@inproceedings{Lessmeier2016,
  author    = {Lessmeier, Christian and Kimotho, James Kuria and Zimmer, Detmar and Sextro, Walter},
  title     = {{Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchamrk Data Set for Data-Driven Classification}},
  booktitle = {Proceedings of the European Conference of the PHM Society},
  year      = {2016},
  url       = {https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter}
}
```

---

## 4. 그 외 보조 데이터셋

- **XJTU-SY**: 15개 베어링의 전 수명 데이터, 다양한 회전속도·하중. RUL 예측에 좋음.
- **FEMTO(PRONOSTIA)**: IEEE PHM 2012 챌린지에서 사용된 RUL 표준 벤치마크 (등록 필요).
- **Paderborn용 파이썬 패키지**: `pip install paderborn-bearing` — 전처리·로딩 자동화 지원.
- **AI4I 2020 (Kaggle)**: 합성 데이터로 진동 시계열이 아님(센서 메트릭스). 예지보전 **개념 소개/간단한 실험**에만 적합. 본 진동 연구의 주 데이터로는 부적합.

---

## 5. 데이터셋 조달 전 체크리스트

- [ ] 각 데이터셋의 **라이선스**(특히 Paderborn CC BY-NC) 확인
- [ ] 샘플링률과 결함 주파수(나이퀴스트) 관계 확인
- [ ] 데이터 크기·다운로드 시간 확인
- [ ] 논문에 인용할 문헌(원문) 확보
- [ ] 데이터 누수 방지 위한 **파일 단위 분할** 계획 수립

---

## 6. 다운로드 바로가기 요약

| 데이터셋 | URL |
|---|---|
| CWRU 공식 | https://engineering.case.edu/bearingdatacenter/download-data-file |
| CWRU Zenodo | https://zenodo.org/records/10987113 |
| CWRU Kaggle | https://www.kaggle.com/datasets/brjapon/cwru-bearing-datasets |
| NASA IMS | https://data.nasa.gov/dataset/ims-bearings |
| NASA PCoE (직접 다운로드) | https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip |
| Paderborn | https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download |
| Paderborn PyPI 패키지 | https://pypi.org/project/paderborn-bearing/ |
