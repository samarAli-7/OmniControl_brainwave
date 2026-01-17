import cv2
import torch
import torch.nn as nn
import mediapipe as mp
from torchvision import transforms
from PIL import Image
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"   # silence TF logs
os.environ["CUDA_VISIBLE_DEVICES"] = "0"   # lock GPU id

# =========================
# 1) CONFIG
# =========================
MODEL_PATH = "Hand_Gestures_MediaPipe_ResNet_v2.pth"

CLASS_NAMES = [
    'Blank', 'Fist', 'Five', 'Four', 'One',
    'Rock_On', 'Spider_man', 'Three', 'Thumb', 'Two'
]

DEVICE = torch.device("cpu")
print("Device:", DEVICE)

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv_path = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(out_channels)
        )

        self.shortcut = nn.Identity()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        return torch.relu(self.conv_path(x) + self.shortcut(x))

class GesturesResNet(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.prep = nn.Sequential(
            nn.Conv2d(3, 16, 3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True)
        )

        self.layer1 = nn.Sequential(ResidualBlock(16, 16, 1), ResidualBlock(16, 32, 2))
        self.layer2 = nn.Sequential(ResidualBlock(32, 32, 1), ResidualBlock(32, 64, 2))
        self.layer3 = nn.Sequential(ResidualBlock(64, 64, 1), ResidualBlock(64, 128, 2))
        self.layer4 = nn.Sequential(ResidualBlock(128, 128, 1), ResidualBlock(128, 256, 2))

        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        x = self.prep(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avg_pool(x)
        return self.fc(x)

# =========================
# 3) LOAD MODEL
# =========================
assert os.path.exists(MODEL_PATH), f"Model not found: {MODEL_PATH}"

model = GesturesResNet(num_classes=len(CLASS_NAMES)).to(DEVICE)
state = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
model.load_state_dict(state)
model.eval()

print("✅ Loaded:", MODEL_PATH)
print("✅ Classes:", CLASS_NAMES)

# =========================
# 4) TRANSFORMS (SAME AS VAL)
# =========================
val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# =========================
# 5) MEDIAPIPE HANDS
# =========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

def get_hand_bbox(hand_landmarks, w, h, pad=40):
    xs = [int(lm.x * w) for lm in hand_landmarks.landmark]
    ys = [int(lm.y * h) for lm in hand_landmarks.landmark]
    x1, x2 = max(min(xs) - pad, 0), min(max(xs) + pad, w)
    y1, y2 = max(min(ys) - pad, 0), min(max(ys) + pad, h)
    return x1, y1, x2, y2

def predict(crop_bgr):
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(crop_rgb)
    x = val_transforms(pil).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(torch.argmax(probs).item())
        conf = float(probs[idx].item())

    return idx, conf

# =========================
# 6) CAMERA LOOP
# =========================
cap = cv2.VideoCapture(0)
print("✅ Running... Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0]
        x1, y1, x2, y2 = get_hand_bbox(lm, w, h)

        crop = frame[y1:y2, x1:x2]
        if crop.size > 0:
            idx, conf = predict(crop)
            label = CLASS_NAMES[idx]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf*100:.1f}%",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("Hand Crop", crop)

    cv2.imshow("Gesture v2 (MediaPipe -> ResNet)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
