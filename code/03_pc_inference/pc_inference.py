"""
PC에서 TFLite(int8) 모델 추론 검증 예제
=======================================
- int8 양자화 TFLite 모델을 PC에서 실행
- 입력/출력 양자화 파라미터 적용
- 정상/이상 판별 및 정확도 평가
"""
import os
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

MODEL_PATH = r"C:\VibrationPMA\tflite_models\model_int8.tflite"
DATA_PATH = r"C:\VibrationPMA\data\cwru_preprocessed.npz"

NUM_CLASSES = 4

# ----------------------------------------------------------------------
# TFLite 인터프리터 로드
# ----------------------------------------------------------------------
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("입력:", input_details)
print("출력:", output_details)

in_scale, in_zero = input_details[0]['quantization']
out_scale, out_zero = output_details[0]['quantization']
input_shape = input_details[0]['shape']

print(f"입력 quantization: scale={in_scale}, zero={in_zero}")
print(f"출력 quantization: scale={out_scale}, zero={out_zero}")

def to_int8(x_float):
    q = x_float / in_scale + in_zero
    return np.clip(q, -128, 127).astype(np.int8)

def from_int8(q_int8):
    return (q_int8.astype(np.float32) - out_zero) * out_scale

def infer_batch(X):
    """X: [N, WINDOW, 1] float32 구현용."""
    preds = []
    for i in range(len(X)):
        x = X[i:i+1].astype(np.float32)
        q = to_int8(x)
        interpreter.set_tensor(input_details[0]['index'], q.reshape(input_shape))
        interpreter.invoke()
        out_q = interpreter.get_tensor(output_details[0]['index'])
        out = from_int8(out_q)
        preds.append(out[0])
    return np.array(preds)

# ----------------------------------------------------------------------
# 평가
# ----------------------------------------------------------------------
data = np.load(DATA_PATH)
X = data["X"]; y = data["y"]

# 대표 일부만 빠르게 (전체면 오래 걸림)
np.random.seed(42)
idx = np.random.choice(len(X), size=2000, replace=False)
X_sub = X[idx][..., np.newaxis]
y_sub = y[idx]

preds = infer_batch(X_sub)
y_pred = preds.argmax(axis=1)

print("\n=== int8 TFLite PC 추론 결과 ===")
print(classification_report(y_sub, y_pred, digits=4))
print("Confusion Matrix:\n", confusion_matrix(y_sub, y_pred))
