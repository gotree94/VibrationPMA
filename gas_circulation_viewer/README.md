# Gas Circulation Process Modifier — 3D Viewer 개발 문서 (1차 완료)

> **파일 위치:** `Tesla_Control_UI/gas_circulation_viewer/`
> **대상 모델:** `Tesla_Control_UI/gas_circulation_process_modifier.glb` (약 6.72MB)
> **실행:** `node server.js` → 브라우저 `http://localhost:3031/gas_circulation_viewer/`

---

## 1. 프로젝트 개요

삼성전자 가스 순환 공정 장비(`gas_circulation_process_modifier`)의 **STEP → GLB** 변환 모델을 웹브라우저에서 실시간 3D로 조회하기 위한 Three.js 뷰어입니다.

- GLB 파일이 아니라 서버(정적 파일 서버)로 서빙합니다 (GLB는 GLTFLoader · CORS 제약으로 `file://` 직접 열기 불가)
- 사용자 요구로 개발된 기능: **좌표계(Z-up) 정렬, 빠른 조작감, 온디맨드 렌더링, 구조 트리, 부품 줌인 + 전체 색상 강조, 트리 파일 저장(TXT/JSON/CSV)**
- 최종 목표(다음 단계): 외부 인터페이스에서 부품명을 받아 해당 부품으로 자동 줌인 + 강조

---

## 2. 파일 구성

| 파일 | 역할 |
|---|---|
| `gas_circulation_viewer/index.html` | Three.js 뷰어 전체 (UI + 셰이더/씬/제어 로직, 단일 파일) |
| `gas_circulation_viewer/server.js` | 정적 파일 서버 (Node.js, 포트 3031) |
| `gas_circulation_process_modifier.glb` | 대상 3D 모델 (약 6.72MB, 7,051,320바이트, 284 노드 / 265 메시) |

---

## 3. 모델(GL B) 분석 결과

> three.js(r159) GLTFLoader 기준으로 RAW glTF 노드, 실제 씬 그래프 두 층을 구분해서 파악해야 합니다.
> **핵심**: GLB 안의 "다중 primitive 메시 노드"는 로더가 `Group` + 자식 메시들로 **분해**합니다.

### 3-1. RAW glTF (GLB 바이너리 JSON)

- 노드 284개, 메시 265개, 재질 20개(`mat_0`~`mat_19`), 씬 1개
- 관심 부품 4개는 RAW 에서 `mesh=true, children=0` (단일 노드):
  - `nut_m011` (노드 278), `nut_m012` (노드 280)
  - `bolt_short_m002` (노드 277), `bolt_short_m003` (노드 279)
- 루트 노드 이름은 인코딩 쓰레기(`\X2\ACF5...\X0\`) → 트리/파일에서 정리 필요

### 3-2. 실제 씬 그래프 (three.js 로드 후) — 분석 코드 (`node test.js`)

`GLTFLoader`는 다중 primitive 메시를 **Group + 자식 Mesh**로 펼치며, 각 자식 메시에 `기본이름_NN` 이름을 매깁니다.

```
nut_m012 (Group)                            ← 선택 대상 (12개 자식)
├─ nut_m12_61  Mesh (59v)   mat_1
├─ nut_m12_62  Mesh (58v)   mat_1
├─ nut_m12_63  Mesh (35v)   mat_1
├─ nut_m12_64  Mesh (59v)   mat_1
├─ nut_m12_65  Mesh (63v)   mat_1
├─ nut_m12_66  Mesh (96v)   mat_1
├─ nut_m12_67~72 Mesh (13v) mat_1 (6개)
```

같은 패턴이 전역으로: `nut_m12_1`~`nut_m12_72` (6개 너트 × 12조각), `bolt_short_m12_25`~`bolt_short_m12_48` 등.

| 관심 부품 | 실제 자식 구조 |
|---|---|
| `nut_m011` | `nut_m12_49` ~ `nut_m12_60` (12개 Mesh) |
| `nut_m012` | `nut_m12_61` ~ `nut_m12_72` (12개 Mesh) |
| `bolt_short_m002` | `bolt_short_m12_25` ~ `bolt_short_m12_36` (12개 Mesh) |
| `bolt_short_m003` | `bolt_short_m12_37` ~ `bolt_short_m12_48` (12개 Mesh) |

> **이 발견이 "부품 일부만 색칠되는 버그"의 근본 원인** — 아래 8절 참고

부품 별 버텍스 패턴: hex 너트면(6개, 59~96v) + 작은 면조각(6개, 13v) = 12조각

---

## 4. index.html — 아키텍처

### 4-1. importmap (three r159)

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.159.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.159.0/examples/jsm/"
  }
}
</script>
```

### 4-2. 좌표계 변환 체인 (Z-up 정렬, 사용자 승인)

STEP 원본은 Y-up. 장비 모델을 "위아래가 뒤집힌 채로" 보이게 되는 문제를 아래 체인으로 해결합니다.

```js
model.rotation.y = Math.PI;              // ① 상하 반전
modelInner = new THREE.Group();
modelInner.rotation.z = -Math.PI;        // ② 수평 -180° (사용자 요구)
modelWrapper = new THREE.Group();
modelWrapper.rotation.x = -Math.PI / 2;  // ③ Z-up 전환
// 계층: scene → modelWrapper(X -90°) → modelInner(Z -180°) → model(Y 180°)
```

### 4-3. 성능 최적화

| 항목 | 값 | 이유 |
|---|---|---|
| 렌더링 방식 | **온디맨드** (`needsRender` dirty flag) | 씬이 고정되어 있어 요청 시에만 렌더 |
| `pixelRatio` | `min(devicePixelRatio, 1.5)` | 고해상도 대형 모니터 안정성 |
| `powerPreference` | `high-performance` | 전용 GPU 우선 |
| `shadowMap` | 기본 OFF + 토글 버튼 | ON 시 느려짐 → 사용자가 선택 |
| OrbitControls | rotate 1.5 / pan 1.6 / zoom 1.5, damping 0.05 | 빠른 조작감 (사용자 승인) |
| `minDistance` | `maxDim * 0.05` | 작은 부품 줌인 허용 |

### 4-4. 렌더 루프

```js
let needsRender = true;
controls.addEventListener('change', () => { needsRender = true; });

function animate() {
  animFrameId = requestAnimationFrame(animate);
  controls.update();
  if (needsRender) { needsRender = false; renderer.render(scene, camera); }
}
```

### 4-5. 조명

- `AmbientLight` 0.6 (베이스)
- `DirectionalLight` (주광, 그림자 생성, 1.2)
- `DirectionalLight` (반대 방향 림, `0x4fc3f7`, 0.5)
- `PointLight` (필, 0.4)

### 4-6. 시점 제어 버튼

- 정면/후면/좌/우/상/하/ISO/리셋 — `setView(dir)` 로 방향 벡터에 기준 거리 곱함
- ISO = 홈 위치 복귀, 캔버스 **더블클릭 = 리셋**

### 4-7. 모델 로딩 & 피팅

```js
function fitModelToView(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  const center = box.getCenter(new THREE.Vector3());
  const size   = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);

  obj.position.x -= center.x;   // ① 수평 중앙 정렬
  obj.position.z -= center.z;
  obj.position.y -= box.min.y;  // ② 바닥 기준 (y=0) 정렬

  const distance = maxDim * 2.2;   // 홈 카메라 거리
  homeCameraPos = new THREE.Vector3(distance*0.7, distance*0.6, distance*0.7);
  homeTarget    = new THREE.Vector3(0, maxDim*0.35, 0);
  ...
}
```

로드 후 콘솔에 구조 덤프 출력 + 통계 패널(메시/버텍스/재질 수) 표시.

---

## 5. 구조 트리 (활성화 시 생성)

### 5-1. 개요

- **「부품 탐색 → 구조 트리」 버튼**으로 열기/닫기 (on-demand, 첫 열 때만 빌드)
- 좌측 상단 패널, `<details>/<summary>` 접이식 트리
- 메시 리프: `◈ 이름 (버텍스수v)`, 그룹: `▸ 이름 (자식수)` / 루트: `🏗 ...`
- 이름 정리 함수 `cn()`: `\X2\...\X0\` 인코딩 쓰레기 제거, 빈 이름 → `(unnamed)`
- 이름 없는 빈 그룹은 `hasMeshDescendant()` 로 필터링해 생략

```js
function treeItem(obj, isRoot) {
  if (obj.isMesh) {
    const el = document.createElement('div');
    el.className = 'tree-leaf';
    el.innerHTML = `◈ ${esc(cn(obj.name))} <span class="leaf-meta">(${vertexCount}v)</span>`;
    el.addEventListener('click', () => selectPart(obj, el));
    return el;
  }
  // 그룹: <details><summary> 클릭 시 전체 선택(하이라이트) + 접기/펼치기
  ...
}
```

`nut_m012`를 펼치면 자식 `nut_m12_61`~`nut_m12_72`가 그대로 보입니다.

---

## 6. 부품 선택 → 줌인 + 전체 색상 강조 (핵심 기능)

### 6-1. 선택 대상 수집 (`collectMeshes`)

```js
function collectMeshes(obj) {
  if (obj.isMesh) return [obj];       // 단일 메시면 그대로
  const meshes = [];
  obj.traverse(c => { if (c.isMesh) meshes.push(c); }); // Group → 자식 전부
  return meshes;
}
```

### 6-2. 선택 + 강조

```js
let selectedMeshes = [];
let selectedEl = null;

function selectPart(obj, el) {
  clearHighlight();
  const meshes = collectMeshes(obj);   // 그룹이면 자식 메시 전부
  selectedMeshes = meshes;
  if (el) { selectedEl = el; el.classList.add('selected'); }
  meshes.forEach(highlightMesh);       // 전부 주황색으로 교체
  focusOn(obj);                        // 전체 범위로 줌
}

function highlightMesh(mesh) {
  mesh.userData._origMaterial = mesh.material;   // 복원용 원본 저장
  mesh.material = new THREE.MeshStandardMaterial({  // 완전 단색 교체
    color: 0xff8800, emissive: 0xff8800, emissiveIntensity: 0.35,
    metalness: 0.1, roughness: 0.4
  });
}
```

> 단색 재질로 **전체 교체**해야 텍스처(금속 맵 등) 때문에 표면 일부만 물드는 문제가 없습니다.

### 6-3. 복원

```js
function clearHighlight() {
  selectedMeshes.forEach(mesh => {
    if (mesh.userData._origMaterial) {
      mesh.material = mesh.userData._origMaterial;  // 원래 재질 복원
      delete mesh.userData._origMaterial;
    }
  });
  selectedMeshes = [];
  if (selectedEl) { selectedEl.classList.remove('selected'); selectedEl = null; }
  needsRender = true;
}
```

### 6-4. 자동 줌 (ease-out 500ms)

```js
function focusOn(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  const center = box.getCenter(...), size = box.getSize(...);
  const dist = Math.max(size.x, size.y, size.z, 0.05) * 3;
  const camDir = camera.position.clone().sub(controls.target).normalize();
  const endPos = center.clone().add(camDir.multiplyScalar(dist));
  animateCamera(camera.position.clone(), controls.target.clone(), endPos, center);
}
```

### 6-5. Name 기반 검색 (`findPart`)

```js
function findPart(name) {
  let obj = model.getObjectByName(name);          // ① 정확 매칭
  if (!obj) model.traverse(o => {                 // ② 정제 이름 폴백
    if (!obj && cn(o.name) === name) obj = o;
  });
  return obj && collectMeshes(obj).length ? obj : null;
}
function focusPartByName(name) {
  const obj = findPart(name);
  if (obj) selectPart(obj, null);
  else console.warn(`부품을 찾지 못함: ${name}`);
}
```

### 6-6. 「관심 부품」 버튼

```html
<button class="part-btn" data-part="nut_m011">nut_m011</button>
... nut_m012, bolt_short_m002, bolt_short_m003
```

```js
document.querySelectorAll('.part-btn').forEach(btn => {
  btn.addEventListener('click', () => focusPartByName(btn.dataset.part));
});
```

**`focusPartByName(name)`는 곧 외부 인터페이스 연동 시 재사용할 확장 포인트입니다.**

---

## 7. 트리 파일 저장 (TXT / JSON / CSV)

「트리 저장」 그룹의 3개 버튼이 `Blob` + `URL.createObjectURL` + `<a download>`로 브라우저에 다운로드합니다.

| 버튼 | 파일 | 내용/용도 |
|---|---|---|
| TXT | `gas_circulation_structure.txt` | 들여쓰기 계층 + 버텍스/재질, 사람이 읽기용 |
| JSON | `gas_circulation_structure.json` | 중첩 `children[]` 구조 + `summary` — 프로그램 파싱용 |
| CSV | `gas_circulation_structure.csv` | 행=오브젝트(부품명/전체 경로/타입/버텍스/재질), Excel용 |

```js
function treeToJson() {
  function toNode(obj) {
    const node = { name: obj.name || '(unnamed)', type: obj.type };
    if (obj.isMesh) {
      node.vertices = countVertices(obj);
      node.materials = materialNamesOf(obj);
    }
    if (obj.children?.length) node.children = obj.children.map(toNode);
    return node;
  }
  return JSON.stringify({
    file: 'gas_circulation_process_modifier.glb',
    generated: new Date().toISOString(),
    summary: { meshes, vertices, materials },
    root: toNode(model)
  }, null, 2);
}
```

CSV는 `csvEscape()`로 `,`, `"`, 개행 문자 포함 이름(`+_shape_adaptor` 등)을 안전하게 처리합니다.

---

## 8. 트러블슈팅 기록

### 8-1. GLB가 `file://`로 안 열림
한계: GLTFLoader가 GLB를 fetch하기 때문에 CORS 위반. → **Node 정적 서버(server.js)로 서빙** 해결.

### 8-2. 모델이 위아래 뒤집히거나 Z축이 안 맞음
STEP 원본 Y-up vs Three.js Y-up + 장비 특성.
→ 사용자 승인을 거쳐 **변환 체인** `rotation.y=π` → `rotation.z=-π` (내부 Group) → `rotation.x=-π/2` (래퍼 Group) 적용.

### 8-3. 애니메이션이 느림 (이전 버전)
계속 렌더링하는 루프 → **온디맨드 렌더링**(더티 플래그) + 조명/픽셀 비율 최적화. 사용자가 "빠르다"고 승인.

### 8-4. 그림자 켜면 격심한 프레임 드랍
→ **기본 OFF**, 버튼으로 ON/OFF 토글.

### 8-5. 서버가 Ctrl+C로 바로 안 죽음
→ `server.close()` + `closeAllConnections()` + 소켓 추적(`connections` Set) + 5초 강제 종료 fallback + SIGINT/SIGTERM 처리.

### 8-6. **부품 일부만 주황색 (가장 중요한 버그)**
증상: `nut_m011` 등 선택 시 해당 부품 표면 일부만 색이 변함.

- 1차 추정: 재질 복제(`clone()`) 후 색상만 tint → 텍스처 맵 덕에 일부만 물듦. → 단색 `MeshStandardMaterial` 완전 교체로 수정해도 계속 부분 표시.
- **근본 원인 (3절):** three.js GLTFLoader가 다중 primitive 메시를 **Group + 자식 Mesh 12개**로 분해. 기존 `resolveMesh()`가 그룹의 **첫 번째 자식만** 반환해 하나만 색칠됨.
- 수정: `collectMeshes()`로 **자식 메시 전부를 수집**해 전체 강조 + 전체 복원.

```js
// BEFORE (bug): 그룹의 첫 메시만 선택
function resolveMesh(o) { /* o.traverse → 첫 isMesh 반환 */ }
// AFTER (fixed): 자식 전부
function collectMeshes(obj) { ... meshes.push(c) ... }
```

### 8-7. 브라우저가 이전 HTML/JS를 캐싱해 변경 미반영
서버 `Cache-Control: no-cache`(재검증)로는 부족 함에 따라 → **`no-store`** 로 변경해 개발 중 항상 최신 파일을 받도록 보장. (서버 재시작 + Ctrl+F5 지침 제공)

---

## 9. 서버 (server.js)

- 포트 `3031`, 루트 = `Tesla_Control_UI` (GLB는 `../gas_circulation_process_modifier.glb` 경로로 제공)
- 403 경로 탈출 방지 (`path.resolve` 검증), MIME 매핑(`.glb` → `model/gltf-binary`)
- **512KB 이상 파일 스트리밍** (`fs.createReadStream`) — GLB 6.72MB 압축 지연 방지
- 연결 추적 Set + 무해종료(graceful shutdown) 처리
- 접속 시 로컬/네트워크 IP, 루트 경로, 초기 메모리를 콘솔에 출력

```js
const PORT = 3031; const HOST = '0.0.0.0';
const PUBLIC = path.join(__dirname, '..');
const STREAM_THRESHOLD = 512 * 1024;   // 큰 파일은 스트림
```

---

## 10. 실행 방법

```powershell
cd C:\Users\Administrator\Desktop\Tesla_Control_UI\gas_circulation_viewer
node server.js
# 브라우저 → http://localhost:3031/gas_circulation_viewer/
```

> 수정 후 반영 확인: 서버 재시작 + **Ctrl+F5** 강력 새로고침.
> `file://`로 직접 열지 말 것 (CORS 오류).

---

## 11. 사용법 요약

| 동작 | 방법 |
|---|---|
| 회전 / 줌 / 이동 | 좌클릭 드래그 / 휠 / 우클릭 드래그 |
| 초기 시점 | 더블클릭 또는 「리셋」 |
| 방향 | 정면/후면/좌/우/상/하/ISO |
| 부품 구조 보기 | 「부품 탐색 → 구조 트리」 |
| 부품 강조 | 트리에서 이름/그룹 클릭 또는 「관심 부품」 버튼 |
| 하이라이트 해제 | 다른 부품 선택 시 자동, 리셋 등 |
| 트리 저장 | TXT / JSON / CSV 버튼 (다운로드) |

---

## 12. 향후 개선 (2차 계획)

1. **외부 인터페이스 연동** — HTTP 엔드포인트(예: `POST /focus { part: "nut_m011" }`) + 폴링 → `focusPartByName()` 재사용으로 자동 줌인 + 강조
2. 부품명 매핑 테이블 — FreeCAD(STEP) 이름 ↔ GLB 씬 이름
3. 하이라이트 색상 커스터마이징, 다중 부품 동시 강조
4. 외부 상태(경고/에러)에 따른 색 구분 (예: 문제 부품은 빨강)

---

*문서 갱신일: 2026-09-10*