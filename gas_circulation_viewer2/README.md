# Gas Circulation Viewer — 2026-09-11 오전 변경 기록

> **위치:** `C:\Users\user\Desktop\gas_circulation_viewer\`
> **수정 파일:** `index.html` (단일 파일, Three.js 뷰어 전체)
> **변경 범위:** CSS 테마 + JS 렌더/피팅 로직 + UI 신규 추가

---

## 0. 한눈에 보기 (요약)

| 번호 | 항목 | 내용 | 관련 코드 |
|---|---|---|---|
| 1 | 밝은 톤 테마 (CSS) | 배경·패널·버튼·트리 전체를 라이트 테마로 전환 | `<style>` 블록 |
| 2 | 밝은 톤 테마 (JS 씬) | 배경색, 안개, 조명, 그라운드, 그리드 밝게 + 모델 재질 밝기 보정(`brightenModel`) | `BACKGROUND`, 조명, `brightenModel()` |
| 3 | 전체 구조물 줌 핏 개선 | 바운딩 스피어 기준으로 FOV·화면비를 고려해 정확히 전체가 들어오도록 개선 | `fitModelToView()` |
| 4 | 초기 줌 슬라이더 (신규) | 시점 제어 패널에 초기 줌을 20~120%로 조절하는 슬라이더 추가 | HTML/CSS/`applyInitialFit()` |
| 5 | 초기 줌 60% + 상향 | 초기 줌 기본값 60%, 중앙 오브젝트를 화면에서 10%→20% 위로 | `initialFitFactor`, `SCREEN_RAISE` |

---

## 1. 밝은 톤 테마 — CSS

### 1-1. `body` 배경·글자색

**변경 전:**
```css
body {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #ffffff;
}
```

**변경 후:**
```css
body {
    background: linear-gradient(135deg, #e9eff7 0%, #d4deeb 100%);
    color: #1e293b;
}
```

### 1-2. 로딩 문구·스피너

- `#loading` 글자색: `#94a3b8` → `#475569`
- `.spinner` 테두리: 어두운 배경용 `rgba(255,255,255,0.1)` → `rgba(15,23,42,0.12)` (상단 색 `#3b82f6` 유지)

```css
#loading {
    ...
    z-index: 1000;
    color: #475569;
}

.spinner {
    border: 4px solid rgba(15, 23, 42, 0.12);
    border-top: 4px solid #3b82f6;
    ...
}
```

### 1-3. 정보/통계/시점 제어 패널

어두운 반투명(`rgba(15,23,42,0.85)`) → 밝은 흰색 반투명 + 밝은 그림자 + 얇은 테두리로 전환. (`#info`, `#stats-panel`, `#view-controls` 공통 적용)

```css
#info,
#stats-panel,
#view-controls {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid #d3dde9;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.25);
}
```

- `#stats-panel h3` 하단선: `#1e3a5f` → `#d3dde9`
- `#stats-panel .stat span` 값 색: `#e2e8f0` → `#0f172a`

### 1-4. 시점 제어 버튼

```css
#view-controls button {
    background: #ffffff;
    border: 1px solid #c5d2e2;
    color: #1e293b;
}

#view-controls button:hover {
    background: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
    transform: translateY(-1px);
}
```

### 1-5. 구조 트리 패널

```css
#tree-panel {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #d3dde9;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.25);
}

.tree-header {
    border-bottom: 1px solid #d3dde9;
}

.tree-header button {
    background: #ffffff;
    border: 1px solid #c5d2e2;
    color: #1e293b;
}

.tree-header button:hover { background: #3b82f6; color: #ffffff; }

#tree-container { color: #334155; }
#tree-container summary:hover,
#tree-container .tree-leaf:hover { background: #e5ebf4; }
```

> 선택 상태(파란 배경 `#3b82f6` + 흰 글자)는 그대로 유지 — 라이트 배경에서도 가독성 OK.

---

## 2. 밝은 톤 테마 — JS 씬

### 2-1. 배경색·안개

```js
const BACKGROUND = 0xe6edf6;                                  // 0x0f172a → 밝은 하늘색

const scene = new THREE.Scene();
scene.background = new THREE.Color(BACKGROUND);
scene.fog = new THREE.Fog(BACKGROUND, 60, 300);               // 20~60 → 60~300 (움게 펼침)
```

### 2-2. 조명 강도 상향

```js
const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);  // 0.6 → 0.85

const sun = new THREE.DirectionalLight(0xffffff, 1.4);        // 1.2 → 1.4
```

### 2-3. 그라운드·그리드

```js
const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0xc3d0e0,                                          // 0x1e293b → 밝은 회청색
    roughness: 0.95,
    metalness: 0.0
});

const grid = new THREE.GridHelper(40, 40, 0x8fa8c4, 0xc6d3e3); // 어두운 파랑 → 밝은 회파랑
```

### 2-4. 모델 재질 밝기 보정 — 신규 함수

**역할:** GLB 로드 후 모든 메시 재질의 어두운 컬러를 밝게 올리고(`lerp`), 과한 금속성을 줄여 라이트 테마에서 잘 보이게 함. 동일 재질은 `Set`으로 중복 처리 방지.

```js
const WHITE_COLOR = new THREE.Color(0xffffff);

function colorLuminance(c) {
    return 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
}

function brightenMaterial(m) {
    if (!m || !('color' in m)) return;
    if (m.color) {
        const lift = THREE.MathUtils.clamp(0.45 + (1 - colorLuminance(m.color)) * 0.4, 0.45, 0.85);
        m.color.lerp(WHITE_COLOR, lift);
    }
    if (typeof m.metalness === 'number') {
        m.metalness = Math.min(m.metalness, 0.25);
    }
    m.needsUpdate = true;
}

function brightenModel(root) {
    const seen = new Set();
    root.traverse((node) => {
        if (!node.isMesh) return;
        const mats = Array.isArray(node.material) ? node.material : [node.material];
        mats.forEach((m) => {
            if (m && !seen.has(m)) {
                seen.add(m);
                brightenMaterial(m);
            }
        });
    });
}
```

> **조정 포인트:** `lift`의 범위 `0.45~0.85`를 바꾸면 밝기 강도 조절 가능 (클수록 밝아짐).

### 2-5. 로드 시 밝기 보정 호출

좌표계 변환 체인(`modelWrapper → modelInner → model`) 조립 후, `fitModelToView` 직전에 호출.

```js
modelWrapper.add(modelInner);

brightenModel(modelWrapper);      // ① 원본 재질 밝게 보정
fitModelToView(modelWrapper);     // ② 전체 구조물 줌 핏
scene.add(modelWrapper);
```

---

## 3. 전체 구조물 줌 핏 개선

트리 최상단(=전체 모델) 선택 시 전체가 화면에 들어오도록, 기존 대략 공식(`maxDim * 2.2`)을 제거하고 **바운딩 스피어의 반지름 + 카메라 FOV·화면 비율**로 정확한 거리를 계산.

```js
function fitModelToView(obj) {
    const box = new THREE.Box3().setFromObject(obj);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 0.01);

    obj.position.x -= center.x;
    obj.position.z -= center.z;
    obj.position.y -= box.min.y;

    const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
    const aspect = window.innerWidth / window.innerHeight;
    const halfHFov = Math.atan(Math.tan(halfFov) * aspect);
    const radius = size.length() * 0.5;
    const fitDistance = radius / Math.min(Math.sin(halfFov), Math.sin(halfHFov)) * 1.15;

    savedFit = { fitDistance, maxDim };
    controls.minDistance = maxDim * 0.02;
    controls.maxDistance = maxDim * 20;
    applyInitialFit();
}
```

**주요 변화:**
- `fitDistance`(100% 전체 프레임 거리)를 `savedFit`에 저장 → 이후 줌 슬라이더에서 재사용
- 최소/최대 줌 범위를 `maxDim * 0.05 ~ * 8` → `maxDim * 0.02 ~ * 20`로 확대 (더 깊은 줌인/아웃 허용)

---

## 4. 초기 줌 슬라이더 (신규 UI)

"초기 시점을 내가 원하는 줌으로 정하고 싶다"는 요구로 추가. 100% = 전체 프레임 기준, 낮을수록 더 줌인.

### 4-1. HTML (시점 제어 패널 내)

```html
<div class="btn-group" style="margin-top: 8px;">
    <h3>초기 줌</h3>
    <div class="zoom-row">
        <input type="range" id="zoom-factor" min="20" max="120" value="60" step="5">
        <span id="zoom-factor-value">60%</span>
    </div>
    <small class="zoom-hint">100% = 전체 프레임, 낮을수록 더 줌인</small>
</div>
```

### 4-2. CSS

```css
#view-controls .zoom-row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
}

#view-controls .zoom-row input[type="range"] {
    flex: 1;
    accent-color: #3b82f6;
}

#view-controls .zoom-row span {
    min-width: 42px;
    text-align: right;
    font-size: 11px;
    color: #475569;
}

#view-controls .zoom-hint {
    width: 100%;
    font-size: 10px;
    color: #8aa0bb;
    margin-top: -2px;
}
```

### 4-3. JS 로직

**전역 상태 추가:**

```js
let initialFitFactor = 0.6;   // 초기 줌 배율 (60%)
let savedFit = null;          // 전체 프레임 계산 결과 저장 { fitDistance, maxDim }
const SCREEN_RAISE = 0.2;     // 화면 상향 비율 (10% → 20%)
```

**카메라 배치를 담당하는 함수 분리** — **`fitModelToView`와 조절 UI가 공유**하고, 슬라이더 변경 시 재호출되어 즉시 반영:

```js
function applyInitialFit() {
    if (!savedFit) return;
    const { fitDistance, maxDim } = savedFit;
    const distance = fitDistance * initialFitFactor;
    homeCameraPos = new THREE.Vector3(distance * 0.7, distance * 0.6, distance * 0.7);
    homeTarget = new THREE.Vector3(0, maxDim * 0.35 - distance * SCREEN_RAISE, 0);

    scene.fog.near = distance * 1.5;
    scene.fog.far = distance * 4;

    camera.position.copy(homeCameraPos);
    controls.target.copy(homeTarget);
    controls.update();
    needsRender = true;
}
```

**슬라이더 이벤트:**

```js
const zoomFactorInput = document.getElementById('zoom-factor');
const zoomFactorValue = document.getElementById('zoom-factor-value');
zoomFactorInput.addEventListener('input', () => {
    initialFitFactor = Number(zoomFactorInput.value) / 100;
    zoomFactorValue.textContent = zoomFactorInput.value + '%';
    applyInitialFit();
});
```

- 「리셋」/「ISO」/더블클릭 → `homeCameraPos`·`homeTarget` 복귀이므로 **슬라이더로 정한 초기 줌·상향이 그대로 유지**됨.

---

## 5. 초기 줌 60% + 중앙 오브젝트 화면 상향

### 5-1. 초기 줌 기본값 60%

- 슬라이더: `value="60"`, 표시값 `60%`
- JS: `initialFitFactor = 0.6`

### 5-2. 중앙 오브젝트 상향 (10% → 20%)

중앙 오브젝트(전체 구조물)를 화면상 더 높게 보이도록 카메라 조준점(`homeTarget`)을 아래로 내림. 상향 비율은 `SCREEN_RAISE` 상수로 제어.

```js
// 변경 전
homeTarget = new THREE.Vector3(0, maxDim * 0.35, 0);

// 변경 후 (0.1 → 0.2 두 차례 적용)
homeTarget = new THREE.Vector3(0, maxDim * 0.35 - distance * SCREEN_RAISE, 0);
```

---

## 6. 실행 / 확인 방법

```powershell
cd C:\Users\user\Desktop\gas_circulation_viewer
npm start
```

- 접속: `http://localhost:3031/`
- 수정 반영: **서버 재시작 + 브라우저 Ctrl+F5** (서버가 `Cache-Control: no-store` 설정이므로 원칙적으로 캐시 없음)

### 주요 튜닝 포인트

| 원하는 것 | 바꿀 위치 |
|---|---|
| 전체 밝기 강도 | `brightenMaterial()`의 `lift` 범위 `0.45~0.85` |
| 배경 하늘색 톤 | `const BACKGROUND` (`0xe6edf6`) |
| 초기 줌 기본값 | 슬라이더 `value` + `initialFitFactor` |
| 오브젝트 상향 정도 | `const SCREEN_RAISE` (`0.2` = 20%) |
| 줌 인/아웃 한계 | `controls.minDistance` / `controls.maxDistance` (`maxDim * 0.02 / * 20`) |