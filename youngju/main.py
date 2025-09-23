import torch
from collections import deque
import numpy as np
import cv2
import image_loader
import torchvision.models as models
import torch.nn as nn 
import torchvision.transforms as T
import onnxruntime as ort
import os
import time
from AI_config import AI_config

transform = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

def save_video(frames, output_dir, label):
    os.makedirs(output_dir, exist_ok=True)

    # 현재 시간을 기반으로 파일 이름 생성
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.mp4"
    filepath = os.path.join(output_dir, filename)

    # 프레임 크기와 fps 정의
    height, width, _ = frames[0].shape
    fps = 15
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    for f in frames:
        out.write(f)

    out.release()
    print(f"💾 Saved video: {filepath}")

def main():
    # -------------------------
    # 모델 불러오기
    # -------------------------
    ort_session = ort.InferenceSession(AI_config.weight_path)
    # -------------------------
    # 프레임 입력
    # -------------------------
    image_path = AI_config.image_path  # 웹캠
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
            frames_tensor = torch.stack(frames).half()       # (T, C, H, W)
            frames_tensor = frames_tensor.unsqueeze(0)  # (1, T, C, H, W)

            with torch.no_grad():
                # (1, T, C, H, W) → numpy 로 변환
                frames_numpy = frames_tensor.cpu().numpy().astype(np.float16)

                # ONNX Runtime 실행
                ort_inputs = {"input": frames_numpy}
                ort_outs = ort_session.run(None, ort_inputs)
                output = torch.tensor(ort_outs[0]).float()   # torch 텐서로 변환하면 기존 코드 재사용 가능

                pred = torch.argmax(output, dim=1).item()

                print("Prediction:", "Accident" if pred==1 else "Non-Accident")
                print("Raw output:", output)
                print("Softmax:", torch.softmax(output, dim=1))
                
                original_frames = list(buffer)
                
                if pred == 1:
                    save_video(original_frames, AI_config.save_accident_path, "accident")
                else:
                    save_video(original_frames, AI_config.save_non_accident_path, "non_accident")

            buffer.clear()

if __name__ == "__main__":
    main()
