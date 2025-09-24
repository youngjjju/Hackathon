import torch
from collections import deque
import numpy as np
import cv2
import torchvision.models as models
import torch.nn as nn
import torchvision.transforms as T
import os
import time
from AI_config import AI_config
import image_loader

# -------------------------
# VideoClassifier 정의
# -------------------------


class VideoClassifier(nn.Module):
    def __init__(self, hidden_dim=256, num_classes=2):
        super(VideoClassifier, self).__init__()

        base_model = models.resnet18(weights=None)  # 학습 때와 동일하게
        modules = list(base_model.children())[:-1]
        self.feature_extractor = nn.Sequential(*modules)
        self.feature_dim = base_model.fc.in_features

        self.lstm = nn.LSTM(self.feature_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        # x: (B, T, C, H, W)
        B, T, C, H, W = x.shape
        x = x.view(B*T, C, H, W)
        feats = self.feature_extractor(x)       # (B*T, feature_dim, 1, 1)
        feats = feats.view(B, T, -1)            # (B, T, feature_dim)
        _, (h_n, _) = self.lstm(feats)          # h_n: (1, B, hidden_dim)
        out = self.fc(h_n[-1])                  # (B, num_classes)
        return out


# -------------------------
# 전처리 정의
# -------------------------
transform = T.Compose([
    T.ToPILImage(),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

# -------------------------
# 비디오 저장 함수
# -------------------------


def save_video(frames, output_dir, label):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.mp4"
    filepath = os.path.join(output_dir, filename)

    height, width, _ = frames[0].shape
    fps = 15
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

    for f in frames:
        out.write(f)

    out.release()
    print(f"💾 Saved video: {filepath}")

# -------------------------
# 추론 메인 함수
# -------------------------


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 모델 불러오기
    model = VideoClassifier(hidden_dim=256, num_classes=2).to(device)
    model.load_state_dict(torch.load(
        AI_config.weight_path, map_location=device))
    model.eval()

    # 프레임 입력
    image_path = AI_config.image_path  # 웹캠 또는 동영상 경로
    loader = image_loader.ImageLoader(image_path, imshow=True)


    buffer_tensor = deque(maxlen=60)  # 모델 입력용
    buffer_raw = deque(maxlen=60)     # 저장용 (numpy frame)
    
    frame_count = 0

    for frame in loader.frame_generator():
        frame_count += 1
        if frame_count % 2 == 0:
            # 저장용: 원본 프레임 그대로
            buffer_raw.append(frame.copy())

            # 추론용: 224x224 resize + transform
            frame_resized = cv2.resize(frame, (224, 224))
            frame_tensor = transform(frame_resized)
            buffer_tensor.append(frame_tensor)

        if len(buffer_tensor) == buffer_tensor.maxlen:
            frames_tensor = torch.stack(list(buffer_tensor))         # (T, C, H, W)
            frames_tensor = frames_tensor.unsqueeze(
                0).to(device)    # (1, T, C, H, W)

            with torch.no_grad():
                output = model(frames_tensor)
                pred = torch.argmax(output, dim=1).item()
                probs = torch.softmax(output, dim=1)

            print("Prediction:", "Accident" if pred == 1 else "Non-Accident")
            print("Raw output:", output)
            print("Softmax:", probs)

            if pred == 1:
                save_video(list(buffer_raw),
                        AI_config.save_accident_path, "accident")
            else:
                save_video(list(buffer_raw),
                        AI_config.save_non_accident_path, "non_accident")

            buffer_tensor.clear()
            buffer_raw.clear()


if __name__ == "__main__":
    main()
