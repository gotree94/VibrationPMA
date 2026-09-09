"""
CWRU 진동 데이터 로딩 예제
===========================
CWRU Bearing Data Center에서 받은 .mat 파일을 읽어,
윈도우(length) 단위의 샘플과 라벨로 변환한다.

사용 전:
  - .mat 파일을 C:\VibrationPMA\data\cwru\ 아래에 폴더별로 정리한다.
    예)
      data/cwru/Normal/    -> 97.mat, 98.mat, ... (정상)
      data/cwru/IR007/      -> 105.mat, ...      (내륜 결함 0.007")
      data/cwru/OR007/      -> 130.mat, ...      (외륜 결함 0.007")
      data/cwru/B007/       -> 118.mat, ...      (볼 결함 0.007")
  - scipy.io로 .mat을 로드한다.

주의:
  - 파일(실험)별 분할을 위해 파일 경로 정보를 함께 반환한다.
  - 데이터 누수 방지를 위해 train/val/test 분할은 파일 단위로 수행해야 한다.
"""
import os
import numpy as np
from scipy.io import loadmat

# ----------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------
DATA_ROOT = r"C:\VibrationPMA\data\cwru"

# 라벨 매핑: 폴더명 -> 클래스 인덱스
CLASS_MAP = {
    "Normal": 0,   # 정상
    "IR007":  1,   # 내륜 결함 inward race, 0.007 inch
    "OR007":  2,   # 외륜 결함 outer race, 0.007 inch
    "B007":   3,   # 전동체(볼) 결함 ball, 0.007 inch
}

# 결함 주파수 확인용: 동기 속도별 회전 주파수 (Hz) -> RPM/60
# 1797 RPM = 29.95 Hz, 1772 = 29.53, 1750 = 29.17, 1730 = 28.83

WINDOW_LEN = 1024     # 윈도우 크기(샘플). 논문 하이퍼파라미터로 실험할 것
SRC_FS = 48000        # 원본 샘플링률 (12kHz 파일은 12000으로 변경)
TGT_FS = 4000         # 다운샘플링 목표 (MCU 경량화 고려)

# ----------------------------------------------------------------------
# .mat 내부 변수명 조회 도우미
# ----------------------------------------------------------------------
def find_variable(mat_dict):
    """.mat 파일에서 진동 시계열이 담긴 변수를 찾아 반환한다.
    CWRU 파일은 'X' 변수 등에 신호가 있다.
    """
    for key in ("X", "DE_time", "FE_time", "data", "vib",
                "__header__", "__version__", "__globals__"):
        if key in mat_dict and isinstance(mat_dict[key], np.ndarray):
            return mat_dict[key]
    # 변수명을 모르는 경우 첫 번째 ndarray를 사용 (위험하므로 경고)
    for key, val in mat_dict.items():
        if isinstance(val, np.ndarray) and val.ndim == 2 and len(val) > 1000:
            print(f"[WARN] 변수명을 추정함: {key}")
            return val
    raise ValueError(f"모르는 .mat 구조: {list(mat_dict.keys())}")


def load_single_mat(filepath):
    """단일 .mat 파일에서 1D 진동 신호(원본 샘플링률) 반환."""
    mat = loadmat(filepath)
    sig = find_variable(mat)
    # CWRU는 (N,1) 또는 (N,) 형태
    sig = np.squeeze(sig).astype(np.float64)
    if sig.ndim != 1:
        # 여러 채널이면 첫 채널만 사용
        sig = sig[:, 0]
    return sig


def decimate(sig, factor):
    """scipy.signal.decimate로 안티앨리어싱 필터를 포함한 다운샘플링."""
    from scipy.signal import decimate
    return decimate(sig, factor, ftype='iir', zero_phase=True)


def sliding_window(sig, window_len):
    """겹침 없는 슬라이딩 윈도우 분할. [N, window_len] 반환."""
    n = len(sig) // window_len
    if n == 0:
        return np.empty((0, window_len))
    return sig[: n * window_len].reshape(n, window_len)


def load_dataset_class(folder, class_idx,
                       window_len=WINDOW_LEN,
                       src_fs=SRC_FS, tgt_fs=TGT_FS):
    """특정 클래스 폴더의 모든 .mat을 로드해 (samples, labels) 반환.
    반환: X:[N,window_len], y:[N], files:(파일별 원본 갯수) 참고용
    """
    samples, labels, meta = [], [], []
    decim_factor = max(1, src_fs // tgt_fs)

    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith((".mat",)):
            continue
        path = os.path.join(folder, fname)
        sig = load_single_mat(path)
        if decim_factor > 1:
            sig = decimate(sig, decim_factor)
        # z-score 정규화
        sig = (sig - sig.mean()) / (sig.std() + 1e-10)
        frames = sliding_window(sig, window_len)
        for fr in frames:
            samples.append(fr)
            labels.append(class_idx)
            meta.append((fname,))   # 출처 파일 기록 (파일 단위 분할에 사용)

    X = np.stack(samples) if samples else np.empty((0, window_len))
    y = np.array(labels, dtype=np.int64)
    return X, y, meta


def load_all_classes(root=DATA_ROOT, window_len=WINDOW_LEN,
                     src_fs=SRC_FS, tgt_fs=TGT_FS):
    """전체 클래스를 읽어 하나의 데이터셋으로 합친다.
    반환: X[N,window_len], y[N], meta(출처파일 리스트), class_names
    """
    X_all, y_all, meta_all = [], [], []
    class_names = []

    for name, idx in CLASS_MAP.items():
        folder = os.path.join(root, name)
        if not os.path.isdir(folder):
            print(f"[SKIP] 폴더 없음: {folder}")
            continue
        X, y, meta = load_dataset_class(folder, idx, window_len, src_fs, tgt_fs)
        if len(X) == 0:
            print(f"[SKIP] 데이터 없음: {folder}")
            continue
        X_all.append(X); y_all.append(y); meta_all.extend(meta)
        class_names.append(name)
        print(f"[OK] {name}: {len(X)} 윈도우")

    X = np.concatenate(X_all, axis=0)
    y = np.concatenate(y_all, axis=0)
    return X, y, meta_all, class_names


if __name__ == "__main__":
    X, y, meta, class_names = load_all_classes()
    print("\n=== 데이터셋 요약 ===")
    print("클래스:", class_names)
    print("입력 shape:", X.shape, "(N, window_len)")
    print("라벨 분포:", np.bincount(y))

    # 저장 (임시) - 추가 처리(파일 단위 분할)는 train_1dcnn에서 수행
    np.savez_compressed(
        r"C:\VibrationPMA\data\cwru_preprocessed.npz",
        X=X, y=y, class_names=np.array(class_names, dtype=object),
    )
    print("저장 완료: data/cwru_preprocessed.npz")
