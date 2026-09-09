"""
TFLite 변환 및 int8 양자화 예제
===============================
- .keras 모델을 TFLite fp32 및 int8 양자화 모델로 변환
- representative dataset 사용
"""
import os
import numpy as np
import tensorflow as tf

MODEL_PATH = r"C:\VibrationPMA\models\model_1dcnn.keras"
FP32_PATH = r"C:\VibrationPMA\tflite_models\model_fp32.tflite"
INT8_PATH = r"C:\VibrationPMA\tflite_models\model_int8.tflite"

# 입력 shape 결정 (모델에서)
model = tf.keras.models.load_model(MODEL_PATH)
print(model.input_shape)   # (None, WINDOW_LEN, 1)

# ----------------------------------------------------------------------
# FP32 변환
# ----------------------------------------------------------------------
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_fp32 = converter.convert()
with open(FP32_PATH, "wb") as f:
    f.write(tflite_fp32)
print("FP32 TFLite 저장:", FP32_PATH, f"({len(tflite_fp32)} bytes)")

# ----------------------------------------------------------------------
# int8 양자화 변환
# ----------------------------------------------------------------------
# 대표 데이터셋 로딩 (전처리된 X 사용)
data = np.load(r"C:\VibrationPMA\data\cwru_preprocessed.npz")
X_calib = data["X"][:2048]  # 대표 데이터 일부

WINDOW_LEN = X_calib.shape[1]

def representative_dataset():
    for i in range(0, len(X_calib), 32):
        batch = X_calib[i:i+32].astype(np.float32)[..., np.newaxis]
        yield [batch]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_int8 = converter.convert()
with open(INT8_PATH, "wb") as f:
    f.write(tflite_int8)
print("int8 TFLite 저장:", INT8_PATH, f"({len(tflite_int8)} bytes)")
print("크기 감소:", len(tflite_fp32), "->", len(tflite_int8),
      "(약 {:.2f}배)".format(len(tflite_fp32)/len(tflite_int8)))
