import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import cv2
import numpy as np
import glob
import torch
import sys
import os
from segment_anything import sam_model_registry, SamPredictor

# YOLO 모델 경로
fashion_model_path = "yolov5/runs/train/exp2/weights/best.pt"
hair_model_path = "runs/train/exp3/weights/best.pt"
fashion_model = torch.hub.load('ultralytics/yolov5', 'custom', path=fashion_model_path)
hair_model = torch.hub.load('ultralytics/yolov5', 'custom', path=hair_model_path)
fashion_model.conf = 0.5
hair_model.conf = 0.3  # 헤어 모델의 신뢰도 임계값을 낮춤

# SAM 모델 경로
sam_checkpoint = "GSA/sam_vit_h.pth"
sam_model = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
sam_predictor = SamPredictor(sam_model)

# 얼굴 탐지를 위한 Haar Cascade 분류기 로드
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 머리 스타일 라벨 정의
hair_labels = [
    "long Curly Hair", "long Straight Hair", "long Wavy Hair", 
    "short curly hair", "short straight hair", "short wavy hair"
]

# 패션 아이템 라벨 정의
fashion_labels = [
    "bag", "dress", "hat", "jacket", "pants", "shirt", "shoe", "shorts", "skirt", "sunglass"
]

def analyze_image(user_name):
    user_directory = os.path.join("C:/Users/DS/human/Pictures", user_name)
    os.makedirs(user_directory, exist_ok=True)

    list_of_files = glob.glob(f"{user_directory}/*.jpg")
    if not list_of_files:
        return {"error": "지정된 폴더에 JPG 이미지가 없습니다."}

    latest_file = max(list_of_files, key=os.path.getctime)
    image = cv2.imread(latest_file)
    if image is None:
        return {"error": "이미지를 불러오지 못했습니다. 경로를 확인하세요."}

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 얼굴 탐지 강화
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
    
    # 패션 아이템 탐지
    fashion_results = fashion_model(image_rgb)

    # 머리 스타일 탐지
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        expand_ratio = 2.0  # 확장 비율 증가
        center_x, center_y = x + w//2, y + h//2
        new_w, new_h = int(w * expand_ratio), int(h * expand_ratio * 2)  # 세로로 더 확장
        x1 = max(0, center_x - new_w//2)
        y1 = max(0, center_y - new_h//2)
        x2 = min(image.shape[1], x1 + new_w)
        y2 = min(image.shape[0], y1 + new_h)
        
        hair_image = image_rgb[y1:y2, x1:x2]
        hair_image_resized = cv2.resize(hair_image, (640, 640))
        
        hair_results = hair_model(hair_image_resized)
    else:
        # 얼굴이 탐지되지 않을 경우, 여러 스케일로 탐지 시도
        scales = [0.5, 0.75, 1.0]
        hair_results = None
        for scale in scales:
            resized_image = cv2.resize(image_rgb, (0, 0), fx=scale, fy=scale)
            results = hair_model(resized_image)
            if len(results.xyxy[0]) > 0:
                hair_results = results
                break
        if hair_results is None:
            hair_results = hair_model(image_rgb)  # 마지막으로 원본 이미지로 시도

    detected_boxes = []
    
    # 패션 아이템 탐지 결과 처리
    for *box, conf, cls in fashion_results.xyxy[0]:
        label = fashion_results.names[int(cls)]
        if label in fashion_labels:
            detected_boxes.append({
                "label": label, 
                "box": [float(coord) for coord in box],
                "confidence": float(conf)
            })
    
    # 머리 스타일 탐지 결과 처리
    if len(faces) > 0:
        for *box, conf, cls in hair_results.xyxy[0]:
            label = hair_results.names[int(cls)]
            if label in hair_labels:
                x_min, y_min, x_max, y_max = [float(coord) for coord in box]
                x_min = x1 + (x_min * (x2-x1) / 640)
                x_max = x1 + (x_max * (x2-x1) / 640)
                y_min = y1 + (y_min * (y2-y1) / 640)
                y_max = y1 + (y_max * (y2-y1) / 640)
                detected_boxes.append({
                    "label": label, 
                    "box": [x_min, y_min, x_max, y_max],
                    "confidence": float(conf)
                })
    else:
        for *box, conf, cls in hair_results.xyxy[0]:
            label = hair_results.names[int(cls)]
            if label in hair_labels:
                x_min, y_min, x_max, y_max = [float(coord) for coord in box]
                if 'scale' in locals():
                    x_min, y_min, x_max, y_max = x_min/scale, y_min/scale, x_max/scale, y_max/scale
                detected_boxes.append({
                    "label": label, 
                    "box": [x_min, y_min, x_max, y_max],
                    "confidence": float(conf)
                })

    if not detected_boxes:
        return {"error": "지정된 객체를 탐지하지 못했습니다."}

    output_txt_path = os.path.join(user_directory, "detected_colors.txt")
    results_with_colors = []

    sam_predictor.set_image(image_rgb)
    for obj in detected_boxes:
        label = obj["label"]
        x_min, y_min, x_max, y_max = map(int, obj["box"])

        input_box = np.array([x_min, y_min, x_max, y_max])
        masks, _, _ = sam_predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box[None, :],
            multimask_output=False,
        )

        mask = masks[0][y_min:y_max, x_min:x_max]
        masked_image = image_rgb[y_min:y_max, x_min:x_max].copy()
        masked_image[~mask] = [0, 0, 0]

        masked_pixels = masked_image[mask]
        if len(masked_pixels) > 0:
            avg_color = np.mean(masked_pixels, axis=0).astype(int)
            avg_color_rgb = tuple(avg_color)
            avg_color_hex = '#{:02x}{:02x}{:02x}'.format(*avg_color)
        else:
            avg_color_hex = '#000000'

        obj["color"] = avg_color_hex
        results_with_colors.append(obj)

        segmented_image = image_rgb[y_min:y_max, x_min:x_max].copy()
        segmented_image[mask] = avg_color
        segmented_output_path = os.path.join(user_directory, f"segmented_{obj['label']}.jpg")
        cv2.imwrite(segmented_output_path, cv2.cvtColor(segmented_image, cv2.COLOR_RGB2BGR))
    
    for obj in results_with_colors:
        x_min, y_min, x_max, y_max = map(int, obj["box"])
        label = obj["label"]
        confidence = obj["confidence"]
        color = obj["color"]
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        label_text = f"{label} ({confidence:.2f}) {color}"
        cv2.putText(image, label_text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    with open(output_txt_path, "w") as f:
        for result in results_with_colors:
            label = result["label"]
            color = result["color"]
            f.write(f"Label: {label}, Hex: {color}\n")

    output_image_path = os.path.join(user_directory, "result_with_boxes.jpg")
    cv2.imwrite(output_image_path, image)

    return {
        "message": f"분석 완료! 바운딩 박스가 포함된 결과 이미지가 '{output_image_path}'에 저장되었습니다.",
        "output_image": output_image_path,
        "output_txt": output_txt_path,
        "results": results_with_colors
    }
