import cv2

def main():
    # 0. 필요한 원본 이미지 파일명 지정
    original_file = 'color_image.jpg'

    # 원본 이미지 불러오기 (읽기 모드로만 가져오므로 원본 파일은 훼손되지 않음)
    img = cv2.imread(original_file)

    if img is None:
        print(f"오류: '{original_file}' 파일을 찾을 수 없습니다. 같은 폴더에 있는지 확인해주세요.")
        return

    # --- 문제 1: 그레이스케일로 변환 ---
    print("1. 그레이스케일 이미지를 출력합니다. (아무 키나 누르면 다음으로 넘어갑니다.)")
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Gray Image', gray_img)
    cv2.imwrite('gray_image.jpg', gray_img)
    cv2.waitKey(0) # 키보드 입력 대기
    cv2.destroyWindow('Gray Image')


    # --- 문제 2: 이미지 크기 변경 (300x300) ---
    print("2. 300x300 크기로 변경된 이미지를 출력합니다.")
    resized_img = cv2.resize(img, (300, 300))
    cv2.imshow('Resized Image', resized_img)
    cv2.imwrite('resized_image.jpg', resized_img)
    cv2.waitKey(0)
    cv2.destroyWindow('Resized Image')


    # --- 문제 3: 이미지 자르기 (50~200px) ---
    # numpy 배열 슬라이싱: img[y시작:y끝, x시작:x끝]
    print("3. 잘라낸(Cropped) 이미지를 출력합니다.")
    cropped_img = img[50:200, 50:200]
    cv2.imshow('Cropped Image', cropped_img)
    cv2.imwrite('cropped_image.jpg', cropped_img)
    cv2.waitKey(0)
    cv2.destroyWindow('Cropped Image')


    # --- 문제 4: 로고 부분(특정 영역) 분리하기 ---
    # cv2.selectROI를 사용하여 webcam 예제처럼 마우스로 영역을 선택
    print("4. 마우스로 로고 영역을 드래그하여 선택한 후 'Space'나 'Enter' 키를 누르세요.")
    
    # 영역 선택 창 띄우기
    roi = cv2.selectROI('Select Logo (Drag and press Enter)', img, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow('Select Logo (Drag and press Enter)')

    # roi는 (x, y, w, h) 형태로 반환됩니다. (선택 안 하면 모두 0)
    if roi != (0, 0, 0, 0):
        x, y, w, h = roi
        # 선택한 영역만큼 원본 이미지에서 슬라이싱하여 추출
        logo_img = img[y:y+h, x:x+w]
        
        cv2.imshow('Extracted Logo', logo_img)
        cv2.imwrite('logo_image.jpg', logo_img)
        print("로고 이미지가 성공적으로 저장되었습니다.")
        cv2.waitKey(0)
        cv2.destroyWindow('Extracted Logo')
    else:
        print("영역이 선택되지 않았습니다.")

    # 모든 창 닫기
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()