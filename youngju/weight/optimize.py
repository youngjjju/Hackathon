from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    model_input="video_classifier_simplified.onnx",
    model_output="video_classifier_fp16.onnx",
    weight_type=QuantType.QInt8  # 또는 QuantType.QUInt8
)