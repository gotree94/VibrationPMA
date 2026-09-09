# 프로젝트 개요 문서

> 이 문서는 논문/발표용으로 정리한 프로젝트 개요이다. 실행 가이드는 `README.md`가 최상위 마스터이다.

## 연구 주제
**진동 시계열 데이터 기반 예지보전 시스템의 경량 딥러닝 모델 설계와 STM32 MCU 엣지 AI 구현**

## 핵심 질문
1. 공개 진동 데이터셋(CWRU, NASA IMS, Paderborn)으로 결함 분류 모델을 얼마나 정확하게 만들 수 있는가?
2. 학습된 모델을 int8 TFLite로 양자화하고 STM32 MCU에 배포했을 때, PC 대비 정확도·속도·메모리는 어떤가?
3. NUCLEO-F411RE(저비용)와 NUCLEO-H753ZI(고성능) 중 어느 것이 본 응용에 적합한가?

## 구성 요소
- **데이터**: 진동(가속도) 시계열
- **모델**: 1D-CNN (경량)
- **변환**: TFLite int8 양자화
- **배포**: STM32Cube.AI → NUCLEO-F411RE / H753ZI
- **평가**: Accuracy, F1, 혼동행렬, 추론시간, 메모리, 전력

## 주요 파일
| 경로 | 내용 |
|---|---|
| `README.md` | 마스터 가이드 (환경→배포→분석) |
| `docs/02_datasets.md` | 데이터셋 조사 |
| `docs/03_setup.md` | 환경 구축 |
| `docs/04_stm32_cubeai_deploy.md` | MCU 배포 |
| `docs/05_thesis_guide.md` | 논문 작성 가이드 |
| `docs/06_results_template.md` | 결과 보고 양식 |
| `code/01_data_preprocessing/` | 전처리·특징추출 |
| `code/02_training/` | 학습·변환 |
| `code/03_pc_inference/` | PC 추론 검증 |
