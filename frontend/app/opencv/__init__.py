"""
OpenCV 예제: Face/Lena는 bounding box 인식용.
PNG 윤곽선 → SVG path 추출은 app.opencv.feather_contour 사용 (깃털.png 등).
"""
import cv2
import os


class FaceDetect:
    def __init__(self):
        # 현재 스크립트 위치 기준으로 데이터 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "..", "data", "opencv")

        self._cascade = os.path.join(data_dir, "haarcascade_frontalface_alt.xml")
        self._girl = os.path.join(data_dir, "girl.jpg")

    def read_file(self):
        cascade = cv2.CascadeClassifier(self._cascade)
        img = cv2.imread(self._girl)
        face = cascade.detectMultiScale(img, minSize=(150, 150))
        if len(face) == 0:
            print("얼굴을 찾을 수 없습니다.")
            quit()
        for idx, (x, y, w, h) in enumerate(face):
            print("얼굴인식 인덱스: ", idx)
            print("얼굴인식 좌표: ", x, y, w, h)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.imwrite("face_detect.jpg", img)
        cv2.imshow("face", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    face_detect = FaceDetect()
    face_detect.read_file()
import cv2
import os


class LenaDetect:
    def __init__(self):
        # 현재 스크립트 위치 기준으로 데이터 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "..", "data", "opencv")

        self._cascade = os.path.join(data_dir, "haarcascade_frontalface_alt.xml")
        self._lena = os.path.join(data_dir, "lena.jpg")

    def read_file(self):
        cascade = cv2.CascadeClassifier(self._cascade)

        # cascade가 제대로 로드되었는지 확인
        if cascade.empty():
            print(f"Cascade를 로드할 수 없습니다: {self._cascade}")
            cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            print("OpenCV 내장 cascade 사용")

        img = cv2.imread(self._lena)

        # 이미지가 제대로 로드되었는지 확인
        if img is None:
            print(f"이미지를 로드할 수 없습니다: {self._lena}")
            return

        print(f"이미지 크기: {img.shape}")

        # 그레이스케일 변환 (CascadeClassifier는 그레이스케일에서 더 잘 작동)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 히스토그램 평활화로 대비 개선
        gray = cv2.equalizeHist(gray)

        # 얼굴 탐지 (레나 이미지는 약간 측면을 향하고 있어 파라미터 조정)
        face = cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        if len(face) == 0:
            print("얼굴을 찾을 수 없습니다.")
            # 이미지를 표시하여 확인
            cv2.imshow("lena", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return

        # 얼굴 영역을 회색으로 변경
        for idx, (x, y, w, h) in enumerate(face):
            print("얼굴인식 인덱스: ", idx)
            print("얼굴인식 좌표: ", x, y, w, h)

            # 얼굴 영역 추출
            face_roi = img[y : y + h, x : x + w]

            # 얼굴 영역을 그레이스케일로 변환
            face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

            # 그레이스케일을 BGR 형식으로 변환 (3채널로)
            face_gray_bgr = cv2.cvtColor(face_gray, cv2.COLOR_GRAY2BGR)

            # 원본 이미지의 얼굴 영역을 회색으로 교체
            img[y : y + h, x : x + w] = face_gray_bgr

        cv2.imwrite("lena_detect.jpg", img)
        cv2.imshow("lena", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # def execute(self):
    #     """이미지를 다양한 형식으로 로드하여 표시"""
    #     original = cv2.imread(self._lena, cv2.IMREAD_COLOR)
    #     gray = cv2.imread(self._lena, cv2.IMREAD_GRAYSCALE)
    #     unchanged = cv2.imread(self._lena, cv2.IMREAD_UNCHANGED)

    #     # 이미지가 제대로 로드되었는지 확인
    #     if original is None:
    #         print(f"이미지를 로드할 수 없습니다: {self._lena}")
    #         return

    #     cv2.imshow("Original", original)
    #     cv2.imshow("Gray", gray)
    #     cv2.imshow("Unchanged", unchanged)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()  # 윈도우종료


if __name__ == "__main__":
    lena_detect = LenaDetect()
    lena_detect.read_file()
    # lena_detect.execute()
