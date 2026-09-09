# STM32Cube.AI 기반 MCU 배포 가이드

본 문서는 PC에서 학습·변환한 `model_int8.tflite` 모델을 **NUCLEO-F411RE** 및 **NUCLEO-H753ZI** 보드에 배포하는 전체 절차를 상세히 기술한다.

---

## 1. 준비물

### 하드웨어
- NUCLEO-F411RE 또는 NUCLEO-H753ZI 보드
- USB Type-A to Micro-B 케이블 (NUCLEO 전원/디버그용)
- (권장) 진동 센서(가속도계) 모듈 — LIS3DSH / ADXL345 / ISM330DHCX 등 (SPI/I2C)
  - 없이도 UART로 사전 저장된 테스트 신호를 주입해 추론 검증 가능

### 소프트웨어 (docs/03_setup.md 참고)
- STM32CubeIDE
- STM32CubeMX
- X-CUBE-AI (또는 STM32Cube AI Studio + ST Edge AI Core, STM32CubeProgrammer)

### 입력 모델
- `C:\VibrationPMA\tflite_models\model_int8.tflite`

---

## 2. 타겟 MCU 선택 가이드

| 항목 | NUCLEO-F411RE | NUCLEO-H753ZI |
|---|---|---|
| 코어 | Cortex-M4F @100MHz | Cortex-M7 @480MHz |
| Flash | 512 KB | 2 MB |
| SRAM | 128 KB | 512 KB |
| 권장 모델 규모 | 경량(수십 KB 이하) | 중간(수백 KB) |
| 실시간성 | 기본 | 우수 (L1 캐시, 고클럭) |

> **제안 흐름**: F411로 먼저 검증 → 성능/용량 부족 시 H753로 확장.

---

## 3. STM32CubeIDE 프로젝트 생성

1. STM32CubeIDE 실행 → `File > New > STM32 Project`
2. 보드 선택:
   - `NUCLEO-F411RE` 또는 `NUCLEO-H753ZI` 검색 후 선택
   - (또는 MCU 직접 선택: STM32F411RET6 / STM32H753ZIT6)
3. 프로젝트명: 예) `vib_pma_f411`
4. Target/Application 설정: 기본값
   - 만약 초기화 코드 생성을 물으면 MFX/시스템 클럭 자동 설정 허용

---

## 4. X-CUBE-AI 연동 (STM32CubeMX 경로)

### 4.1 Middleware 활성화
1. 프로젝트의 `.ioc` 파일 열기 (STM32CubeIDE에서 더블클릭 → STM32CubeMX 열림)
2. 좌측 `Middleware and Software Packs` → **X-CUBE-AI** 체크
3. 설정:
   - **Mode**: `Validation, Benchmark, Generate Code` (또는 `Generate Code`)
   - **Network**: `Add Network`
4. `Network Type`: `TensorFlow Lite`
5. `Tensor Flow File`: `model_int8.tflite` 선택
6. `Network Name`: 예) `network`
7. `Compression`: `1` or `Disabled` (필요 시)
8. 저장

### 4.2 Analyze (성능 예측)
`Analyze` 버튼 → Flash/RAM, 추론 시간(RAM/Flash 비율), MACC 등 리포트 확인.
이 단계에서 모델이 해당 MCU에서 실행 가능한지 판단한다.

### 4.3 Generate Code
STM32CubeMX `Project > Generate Code` 로 C 코드 생성.
`App/network.c`, `App/network_data.c`, `App/network.h`, `App/app_x-cube-ai.c` 등이 생성된다.

---

## 5. STM32Cube AI Studio 경로 (신형, 권장)

1. STM32Cube AI Studio 실행 → 새 프로젝트
2. 타겟 선택: `STM32F411RETx` 또는 `STM32H753ZITx`
3. 툴체인: `STM32CubeIDE`
4. `Model` 탭에서 `model_int8.tflite` 로딩 → Run
5. 리포트(성능·메모리) 확인
6. `Generate code` → STM32CubeMX/IDE와 연동해 프로젝트 생성
- 필요 시 `Run on target`으로 보드에서 직접 검증(val_key 도구 사용)

---

## 6. 응용 애플리케이션 작성

### 6.1 주기 타이머/UART/ADC 설정 (STM32CubeMX)
- **UART**: 디버그 출력 (USART2, PA2/PA3 = NUCLEO ST-Link 가상 COM)
- **ADC/SPI/I2C**: 진동 센서 입력
- **LED**: 판별 결과 표시 (NUCLEO-F411RE: PA5, NUCLEO-H753ZI: PB0)

### 6.2 추론 호출 코드 (사용자 `main` 또는 타이머 콜백)

`app_x-cube-ai.h`가 제공하는 인터페이스 사용 예:

```c
#include "app_x-cube-ai.h"
#include "network.h"
#include "network_data.h"
#include "ai_datatypes_defines.h"

static ai_handle network = AI_HANDLE_NULL;
static ai_network_report net_report;
static ai_buffer ai_input[1];
static ai_buffer ai_output[1];

// 전역 버퍼
static ai_float in_data[AI_NETWORK_IN_1_SIZE];
static ai_float out_data[AI_NETWORK_OUT_1_SIZE];
static ai_i8 in_data_q[AI_NETWORK_IN_1_SIZE];   // int8 입력인 경우
static ai_i8 out_data_q[AI_NETWORK_OUT_1_SIZE]; // int8 출력인 경우
```

```c
// 초기화
static int ai_init(void)
{
    ai_network_params params = {
        .network_data = const_cast<ai_handle_t*>(network_data_weights_get()),
        .network_data_size = AI_NETWORK_DATA_WEIGHTS_SIZE,
    };
    if (!ai_network_create(&network, &params))
        return -1;
    // 입력 버퍼 연결 (fp32 예제; int8이면 ai_array handle 변환 필요)
    ai_input[0].data = in_data;
    ai_input[0].format = AI_BUFFER_FORMAT_FLOAT;
    ai_input[0].n_batches = 1;
    ai_output[0].data = out_data;
    ai_output[0].format = AI_BUFFER_FORMAT_FLOAT;
    ai_output[0].n_batches = 1;
    ai_network_get_info(network, &net_report);
    return 0;
}

// 추론 1회
static int ai_infer(void)
{
    ai_i32 nbatch = ai_network_run(network, ai_input, ai_output);
    if (nbatch != 1) return -1;
    return 0;
}
```

> **int8 경로 주의**: 모델이 int8 입력/출력을 갖는 경우, `.tflite`의 quantization scale/zero_point를 코드에 반영해 실수→int8로 변환해 넣어야 한다. STM32Cube.AI는 FP32 형식을 권장하므로, **입력은 FP32, 내부 int8**으로 두는 것도 방법이다. (양자화 파라미터는 `network.h`/`network_data.h`에서 확인)

### 6.3 메인 루프 예시

```c
#include "main.h"
#include "app_x-cube-ai.h"

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_USART2_UART_Init();
    // ADC/SPI/I2C 센서 초기화

    ai_init();  // AI 네트워크 초기화

    char buf[64];
    while (1)
    {
        // 1) 진동 윈도우 획득 (센서 or 테스트 버퍼)
        read_vibration_window(in_data, AI_NETWORK_IN_1_SIZE);
        // 2) 필요 시 전처리(정규화) - 학습 시와 동일한 방법
        // 3) 추론
        if (ai_infer() == 0)
        {
            // 4) 결과 판별 (argmax)
            int cls = argmax(out_data, AI_NETWORK_OUT_1_SIZE);
            float conf = out_data[cls];
            snprintf(buf, sizeof(buf), "Class=%d conf=%.3f\n", cls, conf);
            HAL_UART_Transmit(&huart2, (uint8_t*)buf, strlen(buf), 100);
            // LED 표시
            if (cls == 0) HAL_GPIO_WritePin(GPIOC, GREEN_LED_Pin, GPIO_PIN_SET);
            else          HAL_GPIO_WritePin(GPIOC, GREEN_LED_Pin, GPIO_PIN_RESET);
        }
        HAL_Delay(10);
    }
}

int argmax(const ai_float *arr, int n)
{
    int m = 0;
    for (int i = 1; i < n; i++) if (arr[i] > arr[m]) m = i;
    return m;
}
```

---

## 7. 빌드 및 플래싱

1. STM32CubeIDE에서 `Build` (Ctrl+B)
2. `Run > Debug` 또는 STM32CubeProgrammer로 `.elf`/`.bin` 플래싱
   - NUCLEO는 ST-Link가 내장되어 USB 플러그만으로 플래싱 가능
3. 터미널(Tera Term/시리얼)에서 UART 출력 확인
   - NUCLEO-F411RE 기본: USART2, 115200 baud

---

## 8. 실시간 성능 측정

### 추론 시간
`ai_network_get_info`의 `n_macc`와 예상 MCPS, 또는 DWT 사이클 카운터:

```c
DWT->CYCCNT = 0;
ai_infer();
uint32_t cycles = DWT->CYCCNT;
float ms = cycles / (float)SystemCoreClock * 1000.0f;
```

- DWT 활성화: `CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk; DWT->CYCCNT = 0; DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;`

### Flash/RAM
- 빌드 시 `Project Properties > C/C++ Build > Tool Settings` 또는 빌드 산출 `.map` 파일에서 확인
- STM32CubeMX Analyze 리포트와 대조

### 전력
- 전원 공급기 또는 보드 저전류 측정점에서 측정

---

## 9. 결과 기록 템플릿

```text
[보드]: NUCLEO-F411RE
[모델]: model_int8.tflite (1D-CNN, window=1024, 4 classes)
[Flash 사용]: XXX KB  (네트워크 + 펌웨어)
[RAM 사용]:  XXX KB
[추론 시간]: XX ms
[실시간 FPS]: 약 XX
[정확도(테스트 세트 MCU)]: XX.X %
[전력]: XX mW
```

---

## 10. 자주 묻는 문제

**Q. Analyze에서 Flash/RAM 초과 발생**
- 윈도우 길이 축소, 모델 채널/필터 축소, int8 양자화 확인, 또는 H753으로 마이그레이션.

**Q. int8 모델이 X-CUBE-AI에서 안 읽혀요**
- `.tflite`의 ops가 지원 여부 확인. 불필요한 ops 제거. `converter.target_spec.supported_ops`를 TFLITE_BUILTINS_INT8로.
- 불가 시 FP32 `.tflite`로 배포 후 메모리 확인.

**Q. 실시간 신호 획득과 추론 타이밍 불일치**
- 정확한 윈도우 경계에 맞춰 버퍼를 채우고 추론을 트리거하는 구조 필요.
