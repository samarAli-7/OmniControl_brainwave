import cv2
import numpy as np
import mediapipe as mp


CAM_INDEX = 0
SMOOTH = 7          
DILATE = 2         
ERODE = 1          


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)


HAND_CONNECTIONS = list(mp_hands.HAND_CONNECTIONS)

def landmark_to_px(lm, w, h):
    return int(lm.x * w), int(lm.y * h)

def draw_thick_lines_mask(mask, points, connections, thickness=18):

    for a, b in connections:
        x1, y1 = points[a]
        x2, y2 = points[b]
        cv2.line(mask, (x1, y1), (x2, y2), 255, thickness)

def fill_hand_from_lines(line_mask):
   
    kernel = np.ones((9, 9), np.uint8)
    closed = cv2.morphologyEx(line_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

  
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(line_mask)

    if contours:
        biggest = max(contours, key=cv2.contourArea)
        cv2.drawContours(filled, [biggest], -1, 255, cv2.FILLED)

    return filled



cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("[INFO] Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

   
    final_mask = np.zeros((h, w), dtype=np.uint8)

    if res.multi_hand_landmarks:
        hand_landmarks = res.multi_hand_landmarks[0]

        pts = [landmark_to_px(lm, w, h) for lm in hand_landmarks.landmark]

        line_mask = np.zeros((h, w), dtype=np.uint8)
        draw_thick_lines_mask(line_mask, pts, HAND_CONNECTIONS, thickness=22)

      
        hand_blob = fill_hand_from_lines(line_mask)

        hand_blob = cv2.GaussianBlur(hand_blob, (SMOOTH, SMOOTH), 0)
        _, hand_blob = cv2.threshold(hand_blob, 127, 255, cv2.THRESH_BINARY)

        kernel2 = np.ones((5, 5), np.uint8)
        hand_blob = cv2.erode(hand_blob, kernel2, iterations=ERODE)
        hand_blob = cv2.dilate(hand_blob, kernel2, iterations=DILATE)

        final_mask = hand_blob

    silhouette = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)

    cv2.imshow("Original", frame)
    cv2.imshow("Hand Silhouette", silhouette)

    if (cv2.waitKey(1) & 0xFF) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
