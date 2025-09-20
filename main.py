import torch
from collections import deque
import numpy as np
import cv2
from youngju import image_loader
import torchvision.models as models
import torch.nn as nn 
import torchvision.transforms as T
import onnxruntime as ort

transform = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

# -------------------------
# 학습 시 정의한 모델 다시 선언
# -------------------------

def main():
    # -------------------------
    # 모델 불러오기
    # -------------------------
    ort_session = ort.InferenceSession("/home/youngju/Hackathon/youngju/weight/video_classifier.onnx")
    # -------------------------
    # 프레임 입력
    # -------------------------
    image_path = 0  # 웹캠
    loader = image_loader.ImageLoader(image_path, imshow=True)
    buffer = deque(maxlen=60)
    frame_count = 0
    
    for frame in loader.frame_generator():
        frame_count += 1
        if frame_count % 2 == 0:
            buffer.append(frame)

        if len(buffer) == buffer.maxlen:
            frames = [cv2.resize(f, (224,224)) for f in buffer]
            frames = [transform(f) for f in frames]   # 리스트 형태로 transform 적용
            frames_tensor = torch.stack(frames)       # (T, C, H, W)
            frames_tensor = frames_tensor.unsqueeze(0)  # (1, T, C, H, W)

            with torch.no_grad():
                # (1, T, C, H, W) → numpy 로 변환
                frames_numpy = frames_tensor.numpy()

                # ONNX Runtime 실행
                ort_inputs = {"input": frames_numpy}
                ort_outs = ort_session.run(None, ort_inputs)
                output = torch.tensor(ort_outs[0])   # torch 텐서로 변환하면 기존 코드 재사용 가능

                pred = torch.argmax(output, dim=1).item()
                print("Prediction:", "Accident" if pred==1 else "Non-Accident")
                print("Raw output:", output)
                print("Softmax:", torch.softmax(output, dim=1))

            buffer.clear()

if __name__ == "__main__":
    main()
