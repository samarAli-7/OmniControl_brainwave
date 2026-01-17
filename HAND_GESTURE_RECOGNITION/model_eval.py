import cv2
import mediapipe as mp
import os
import csv

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5)

data_path = 'fist_brown_glove'
output_file = 'landmarks.csv'

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    for label in os.listdir(data_path):
        label_path = os.path.join(data_path, label)
        if not os.path.isdir(label_path): continue
        
        for img_name in os.listdir(label_path):
            img = cv2.imread(os.path.join(label_path, img_name))
            results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
            if results.multi_hand_landmarks:
                landmarks = []
                for lm in results.multi_hand_landmarks[0].landmark:
                    landmarks.extend([lm.x, lm.y, lm.z]) # 63 values total
                writer.writerow([label] + landmarks)