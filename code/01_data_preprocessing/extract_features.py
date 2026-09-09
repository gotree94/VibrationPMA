"""
특징 추출 및 파일 단위 데이터 분할 예제
=====================================
- 시간 영역 / 주파수 영역 통계 특징을 추출(전통 ML 비교 실험용)
- 파일 단위 train/val/test 분할 (데이터 누수 방지)
"""
import os
import numpy as np
from scipy import stats
from sklearn.model_selection import train_test_split


# ----------------------------------------------------------------------
# 1) 파일 단위 분할 헬퍼
# ----------------------------------------------------------------------
def split_by_file(X, y, meta, val_ratio=0.15, test_ratio=0.15, random_seed=42):
    """meta의 파일명 기준으로 파일을 나눠서 분할한다 (데이터 누수 방지).

    동일 파일에서 나온 모든 윈도우가 같은 파티션에 속한다.
    반환: (Xtr,ytr), (Xva,yva), (Xte,yte)
    """
    # 고유 파일명 목록
    files = sorted(set(m[0] for m in meta))
    rng = np.random.RandomState(random_seed)
    rng.shuffle(files)

    n = len(files)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)
    test_files = set(files[:n_test])
    val_files = set(files[n_test:n_test + n_val])

    idx_tr, idx_va, idx_te = [], [], []
    for i, m in enumerate(meta):
        f = m[0]
        if f in test_files:
            idx_te.append(i)
        elif f in val_files:
            idx_va.append(i)
        else:
            idx_tr.append(i)

    return (X[idx_tr], y[idx_tr]), (X[idx_va], y[idx_va]), (X[idx_te], y[idx_te])


# ----------------------------------------------------------------------
# 2) 특징 추출
# ----------------------------------------------------------------------
def time_domain_features(x):
    """시간 영역 통계 특징. 입력 x: 1D 배열 -> (n_ft,)"""
    rms = np.sqrt(np.mean(x ** 2))
    peak = np.max(np.abs(x))
    return np.array([
        np.mean(x),
        np.std(x),
        rms,
        stats.kurtosis(x),      # 첨도
        stats.skew(x),          # 왜도
        peak,                   # 피크
        peak / (rms + 1e-12),   # 파고율 Crest Factor
        np.ptp(x),              # 피크-피크
    ])


def freq_domain_features(x, fs):
    """주파수 영역 특징. FFT 기반 스펙트럼의 중심/확산 등을 추출."""
    N = len(x)
    spec = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    mag = spec / (N / 2.0)          # 정규화
    total = mag.sum() + 1e-12

    # 중심 주파수
    centroid = (freqs * mag).sum() / total
    # 주파수 표준편차(확산)
    spread = np.sqrt(((freqs - centroid) ** 2 * mag).sum() / total)
    # 최대 피크 주파수
    peak_freq = freqs[np.argmax(mag)]

    # 주파수 대역 에너지 (예: 0-500, 500-1000, 1000-2000, 2000-4000 Hz)
    band_edges = [0, 500, 1000, 2000, fs / 2]
    band_energy = []
    for a, b in zip(band_edges[:-1], band_edges[1:]):
        m = (freqs >= a) & (freqs < b)
        band_energy.append((mag[m] ** 2).sum())

    return np.concatenate([np.array([total, centroid, spread, peak_freq]),
                           np.array(band_energy)])


def extract_features(X, fs=4000):
    """전체 데이터셋에 대해 특징을 추출. X:[N,window] -> F:[N, n_f]
    X가 z-score 정규화된 [N, window] 형태라고 가정.
    """
    feats = []
    for x in X:
        t = time_domain_features(x)
        f = freq_domain_features(x, fs)
        feats.append(np.concatenate([t, f]))
    return np.array(feats, dtype=np.float32)


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    data = np.load(r"C:\VibrationPMA\data\cwru_preprocessed.npz",
                   allow_pickle=True)
    X, y = data["X"], data["y"]
    # meta는 npz에 저장 안 했으므로, 여기서는 파일 단위 분할을 위해
    # load_cwru에서 meta를 다시 얻거나, npz에 meta를 저장하도록 확장한다.
    # 간단히 이미 저장된 X,y로 특징만 추출해본다.
    print("특징 추출 중...")
    F = extract_features(X)
    print("특징 shape:", F.shape)
    np.save(r"C:\VibrationPMA\data\cwru_features.npy", F)
    np.save(r"C:\VibrationPMA\data\cwru_labels.npy", y)
    print("저장 완료")
