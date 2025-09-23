import onnx
from onnxconverter_common import float16

# 원본 ONNX 모델 로드
model = onnx.load("video_classifier.onnx")

# FP32 → FP16 변환
model_fp16 = float16.convert_float_to_float16(model)

# 변환된 모델 저장
onnx.save(model_fp16, "video_classifier_fp16.onnx")
