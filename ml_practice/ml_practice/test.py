import cv2
import os

# print(cv2.__version__)

# ===============================================
# 리사이즈

# img1 = cv2.imread('color_image.jpg')
# img1 = cv2.resize(img1, (640, 480))
path = os.getcwd()
# cv2.imwrite(path + '/' + 'resized_image2.jpg', img1)

# =================================================
# 그레이스케일로 변환 
# img1 = cv2.imread('resized_image2.jpg')
# img2 = cv2.imread('resized_image2.jpg', cv2.IMREAD_GRAYSCALE)

# cv2.imshow('image1', img1)
# cv2.imshow('image2', img2)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# ==============================================
# 그레이스케일로 변환 및 퀄리티(화질) 변경

# src_file_name = 'resized_image2.jpg'
# dst1_file_name = 'resized_image2_gray1.jpg'
# dst2_file_name = 'resized_image2_gray2.jpg'

# img2 = cv2.imread(src_file_name, cv2.IMREAD_GRAYSCALE)
# cv2.imwrite(path + '/' + dst1_file_name, img2)
# cv2.imwrite(path + '/' + dst2_file_name, img2, [cv2.IMWRITE_JPEG_QUALITY, 10])

# ============================================
# 위아래로 이어 붙이기

# img1 = cv2.imread('resized_image2.jpg')
# img2 = cv2.imread('resized_image2_gray1.jpg')

# img3 = cv2.hconcat([img1, img2])
# img4 = cv2.vconcat([img1, img2])

# cv2.imshow('image3', img3)
# cv2.imshow('image4', img4)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# ==============================================
# resize 

# img1 = cv2.imread('resized_image2.jpg')

# w = img1.shape[1]
# h = img1.shape[0]

# print(w)
# print(h)

# width = round(w/2)
# height = round(h/2)

# img1 = cv2.resize(img1, (width, height))

# cv2.imshow('image1', img1)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# ===============================================
# 밝기조절 잘못되는 버전 
# img1 = cv2.imread('resized_image2.jpg')

# img2 = img1 + 50
# img3 = img1 - 50

# img4 = cv2.hconcat([img1, img2, img3])

# cv2.imshow('image4', img4)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# =================================================
#밝기 조절

# img1 = cv2.imread('resized_image2.jpg')

# import numpy as np

# img2 = np.clip(img1.astype('int32')+50, 0, 255).astype('uint8')
# img3 = np.clip(img1.astype('int32')-50, 0, 255).astype('uint8')
# img4 = cv2.hconcat([img1, img2, img3])

# cv2.imshow('image4', img4)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# =========================================================
# 회전

# img1 = cv2.imread('resized_image2.jpg')
# height, width, channel = img1.shape
# matrix = cv2.getRotationMatrix2D((width/2, height/2), -45, 0.5)
# dst = cv2.warpAffine(img1, matrix, (width, height))

# cv2.imshow("rotation image", dst)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


# ========================================================
# 좌우반전 상하반전
# img1 = cv2.imread('resized_image2.jpg')

# cv2.imshow("Flip example 1", cv2.flip(img1, 0))
# cv2.imshow("Flip example 2", cv2.flip(img1, 1))
# cv2.imshow("Flip example 3", cv2.flip(img1, -1))

# cv2.waitKey(0)
# cv2.destroyAllWindows()

# ================================================
# 크롭

img1 = cv2.imread('resized_image2.jpg')
img2 = img1[200:400, 200:400].copy()

cv2.imshow('image1', img1)
cv2.imshow('image2', img2)
cv2.waitKey(0)
cv2.destroyAllWindows()