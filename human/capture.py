import cv2
import os
from datetime import datetime

def capture_photo(user_name):
    save_directory = os.path.join("C:/Users/DS/human/Pictures", user_name)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return {"error": "웹캠을 열 수 없습니다."}

    while True:
        ret, frame = cap.read()
        if not ret:
            return {"error": "프레임을 캡처하지 못했습니다."}

        cv2.imshow('Webcam (Press SPACE to capture, ESC to quit)', frame)

        key = cv2.waitKey(1)
        if key == 32:  # SPACE key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"webcam_{timestamp}.jpg"
            filepath = os.path.join(save_directory, filename)
            cv2.imwrite(filepath, frame)
            cap.release()
            cv2.destroyAllWindows()
            return {"message": f"사진이 저장되었습니다: {filepath}", "filepath": filepath}
        elif key == 27:  # ESC key
            cap.release()
            cv2.destroyAllWindows()
            return {"error": "캡처를 취소했습니다."}

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 테스트를 위한 코드
    result = capture_photo("test_user")
    print(result)
