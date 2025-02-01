# 환경 설정
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import cv2
import numpy as np
from segment_anything import sam_model_registry, SamPredictor
from PIL import Image

# YOLO 모델 경로 (vscode 작업 폴더 내 YOLOv5 디렉토리 기준)
yolo_model_path = "yolov5/runs/train/exp2/weights/best.pt"
yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path=yolo_model_path)
yolo_model.conf = 0.5

# SAM 모델 경로 (vscode 작업 폴더 내 GSA 디렉토리 기준)
sam_checkpoint = "GSA/sam_vit_h.pth"
sam_model = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
sam_predictor = SamPredictor(sam_model)

# 이미지 로드
image_path = "C:/Users/DS/human/fashion/extracted_clothes/hi.jpg"
image = cv2.imread(image_path)
if image is None:
    print("이미지를 불러오지 못했습니다. 경로를 확인하세요.")
    exit()

# YOLO 모델에 이미지 전달 (BGR 이미지를 RGB로 변환)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
results = yolo_model(image_rgb)

# YOLO 바운딩 박스 추출
labels_of_interest = ["bag", "dress", "hat", "jacket", "pants", "shirt", "shoe", "shorts", "skirt", "sunglass"]
detected_boxes = []
for *box, conf, cls in results.xyxy[0]:
    label = results.names[int(cls)]
    if label in labels_of_interest:
        detected_boxes.append({"label": label, "box": box, "confidence": conf})

if not detected_boxes:
    print("지정된 객체를 탐지하지 못했습니다.")
    exit()

# SAM 세그멘테이션 수행 및 색상 분석
output_txt_path = "detected_colors.txt"
results_with_colors = []

sam_predictor.set_image(image_rgb)
for obj in detected_boxes:
    label = obj["label"]
    x_min, y_min, x_max, y_max = map(int, obj["box"])

    # SAM으로 세그멘테이션 마스크 생성
    input_box = np.array([x_min, y_min, x_max, y_max])
    masks, _, _ = sam_predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box[None, :],
        multimask_output=False,
    )

    # 마스크 적용 (바운딩 박스 영역에 대해서만)
    mask = masks[0][y_min:y_max, x_min:x_max]
    masked_image = image_rgb[y_min:y_max, x_min:x_max].copy()
    masked_image[~mask] = [0, 0, 0]  # 마스크 외부를 검은색으로

    # 색상 계산 (마스크 영역의 평균 RGB 값)
    masked_pixels = masked_image[mask]
    if len(masked_pixels) > 0:
        avg_color = np.mean(masked_pixels, axis=0).astype(int)
        avg_color_rgb = tuple(avg_color)
        avg_color_hex = '#{:02x}{:02x}{:02x}'.format(*avg_color)
    else:
        avg_color_hex = '#000000'  # 마스크 영역이 없는 경우 검은색으로 처리

    # 결과 저장
    obj["color"] = avg_color_hex
    results_with_colors.append(obj)

    # 세그멘테이션된 이미지 저장
    segmented_image = image_rgb[y_min:y_max, x_min:x_max].copy()
    segmented_image[mask] = avg_color
    segmented_output_path = f"segmented_{obj['label']}.jpg"
    cv2.imwrite(segmented_output_path, cv2.cvtColor(segmented_image, cv2.COLOR_RGB2BGR))
    
# 바운딩 박스와 레이블 추가한 이미지 생성
for obj in results_with_colors:
    x_min, y_min, x_max, y_max = map(int, obj["box"])
    label = obj["label"]
    confidence = obj["confidence"]
    color = obj["color"]
    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
    label_text = f"{label} ({confidence:.2f}) {color}"
    cv2.putText(image, label_text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# 결과를 텍스트 파일에 저장
with open(output_txt_path, "w") as f:
    for result in results_with_colors:
        label = result["label"]
        color = result["color"]
        f.write(f"Label: {label}, Hex: {color}\n")

# 결과 이미지 저장
output_image_path = "result_with_boxes.jpg"
cv2.imwrite(output_image_path, image)

print(f"분석 완료! 바운딩 박스가 포함된 결과 이미지가 '{output_image_path}'에 저장되었습니다.")
print(f"탐지 결과가 '{output_txt_path}'에 저장되었습니다.")
