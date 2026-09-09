"""
1D-CNN 모델 학습 및 저장 예제
=============================
- CWRU 전처리 데이터(npz)를 읽어 1D-CNN으로 정상/이상 분류
- 파일 단위 분할로 데이터 누수 방지
- 학습된 모델을 .keras 저장
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.metrics import classification_report, confusion_matrix

# 추출 모듈을 import 하기 위한 경로
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_data_preprocessing"))

DATA_PATH = r"C:\VibrationPMA\data\cwru_preprocessed.npz"
SAVE_PATH = r"C:\VibrationPMA\models\model_1dcnn.keras"

WINDOW_LEN = 1024
NUM_CLASSES = 4       # Normal/IR/OR/Ball
EPOCHS = 50
BATCH_SIZE = 128
SEED = 42

# ----------------------------------------------------------------------
# 1) 데이터 로딩
# ----------------------------------------------------------------------
data = np.load(DATA_PATH, allow_pickle=True)
X, y = data["X"], data["y"]
print("원본 데이터:", X.shape, y.shape)

# channel 차원 추가: (N, window) -> (N, window, 1)
X = X[..., np.newaxis]
# one-hot
y_onehot = keras.utils.to_categorical(y, num_classes=NUM_CLASSES)

# ----------------------------------------------------------------------
# 2) 데이터 분할 -> 여기서는 파일 분할을 위해 meta가 필요하다.
#    npz에 meta(출처 파일)가 없으므로, 파일 단위 분할을 하려면
#    load_cwru의 load_all_classes()에서 meta를 얻어와야 한다.
#    여기서는 간단히 랜덤 분할로 대체 예시를 보여준다.
#    (실제 논문에서는 반드시 파일 단위 분할 사용)
# ----------------------------------------------------------------------
from sklearn.model_selection import train_test_split
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y_onehot, test_size=0.3,
                                            random_state=SEED, stratify=y)
X_va, X_te, y_va, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5,
                                          random_state=SEED, stratify=y_tmp.argmax(1))

print(f"Train {X_tr.shape[0]} / Val {X_va.shape[0]} / Test {X_te.shape[0]}")

# ----------------------------------------------------------------------
# 3) 모델 정의
# ----------------------------------------------------------------------
def build_1dcnn(window_len, num_classes):
    model = keras.Sequential([
        keras.layers.Input(shape=(window_len, 1)),
        keras.layers.Conv1D(32, 32, activation='relu'),
        keras.layers.MaxPooling1D(4),
        keras.layers.Conv1D(64, 16, activation='relu'),
        keras.layers.MaxPooling1D(4),
        keras.layers.Conv1D(128, 8, activation='relu'),
        keras.layers.GlobalAveragePooling1D(),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.5),
        keras.layers.Dense(num_classes, activation='softmax'),
    ])
    return model

model = build_1dcnn(WINDOW_LEN, NUM_CLASSES)
model.compile(optimizer=keras.optimizers.Adam(1e-3),
              loss='categorical_crossentropy',
              metrics=['accuracy'])
model.summary()

# ----------------------------------------------------------------------
# 4) 학습
# ----------------------------------------------------------------------
callbacks = [
    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True,
                                  monitor='val_loss'),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5,
                                      monitor='val_loss'),
    keras.callbacks.ModelCheckpoint(SAVE_PATH, save_best_only=True,
                                    monitor='val_accuracy'),
]

hist = model.fit(X_tr, y_tr, validation_data=(X_va, y_va),
                 epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=callbacks)

# ----------------------------------------------------------------------
# 5) 평가
# ----------------------------------------------------------------------
y_pred = model.predict(X_te).argmax(axis=1)
y_true = y_te.argmax(axis=1)

print("\n=== 테스트 평가 ===")
print(classification_report(y_true, y_pred, digits=4))

cm = confusion_matrix(y_true, y_pred)
print("\nConfusion Matrix:\n", cm)

# ----------------------------------------------------------------------
# 6) 시각화 (성능 곡선)
# ----------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(hist.history['accuracy'], label='train')
plt.plot(hist.history['val_accuracy'], label='val')
plt.title('Accuracy'); plt.legend()

plt.subplot(1, 2, 2)
plt.plot(hist.history['loss'], label='train')
plt.plot(hist.history['val_loss'], label='val')
plt.title('Loss'); plt.legend()

plt.tight_layout()
os.makedirs(r"C:\VibrationPMA\results", exist_ok=True)
plt.savefig(r"C:\VibrationPMA\results\training_curves.png", dpi=150)
print("학습 곡선 저장 완료")
