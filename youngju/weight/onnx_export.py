import torch
import torch.nn as nn
import torchvision.models as models

# -------------------------
# 모델 정의 (학습할 때와 동일)
# -------------------------
class VideoClassifier(nn.Module):
    def __init__(self, hidden_dim=256, num_classes=2):
        super(VideoClassifier, self).__init__()
        base_model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        modules = list(base_model.children())[:-1]
        self.feature_extractor = nn.Sequential(*modules)
        self.feature_dim = base_model.fc.in_features
        self.lstm = nn.LSTM(self.feature_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        B, T, C, H, W = x.shape
        x = x.view(B*T, C, H, W)
        feats = self.feature_extractor(x)
        feats = feats.view(B, T, -1)
        _, (h_n, _) = self.lstm(feats)
        out = self.fc(h_n[-1])
        return out

# -------------------------
# 최적화/변환 실행
# -------------------------
if __name__ == "__main__":
    model = VideoClassifier(hidden_dim=256, num_classes=2)
    state_dict = torch.load("/home/youngju/Hackathon/youngju/weight/video_classifier.pth",
                            map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    # 예시 입력 (배치1, 타임스텝60, 채널3, 224x224)
    example_input = torch.randn(1, 60, 3, 224, 224)

    # (1) TorchScript 변환
    traced = torch.jit.trace(model, example_input)
    traced.save("video_classifier_traced.pt")

    # (2) ONNX 변환
    torch.onnx.export(model, example_input, "video_classifier.onnx",
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch_size"}})

    print("✅ 최적화된 모델 저장 완료 (TorchScript .pt, ONNX .onnx)")
