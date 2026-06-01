import math
from collections import Counter

def euclidean_distance(point1, point2):
    distance = 0.0
    for i in range(len(point1)):
        distance += (point1[i] - point2[i]) ** 2
    return math.sqrt(distance)

def get_neighbors(train_data, test_point, k):
    distances = []
    for train_point in train_data:
        # train_point[:-1]을 사용하여 마지막 카테고리(라벨)를 제외하고 거리 계산
        distance = euclidean_distance(test_point, train_point[:-1])
        distances.append((train_point, distance))

    # 거리를 기준으로 오름차순 정렬
    distances.sort(key=lambda x: x[1])

    # 가장 가까운 k개의 이웃 추출
    neighbors = []
    for i in range(k):
        neighbors.append(distances[i][0])

    return neighbors

def predict_classification(neighbors):
    # 이전에 수정한 대로 neighbor[-1]을 사용하여 카테고리 라벨만 추출
    output_values = [neighbor[-1] for neighbor in neighbors]
    prediction = Counter(output_values).most_common(1)[0][0]
    return prediction

def knn(train_data, test_point, k):
    neighbors = get_neighbors(train_data, test_point, k)
    prediction = predict_classification(neighbors)
    return prediction

if __name__ == '__main__':
    # 이미지에서 추출한 학습 데이터
    train_data = [
        [300, 150, 50, 1.2, 20, 'A'],
        [310, 145, 55, 1.3, 22, 'A'],
        [290, 152, 48, 1.1, 19, 'A'],
        [250, 100, 60, 0.8, 12, 'B'],
        [255, 98, 62, 0.85, 11, 'B'],
        [260, 105, 59, 0.9, 13, 'B'],
        [320, 160, 45, 1.5, 25, 'A'],
        [245, 90, 63, 0.75, 10, 'B'],
        [280, 130, 70, 1.0, 15, 'C'],
        [285, 135, 68, 1.05, 16, 'C'],
        [275, 120, 65, 1.0, 14, 'C'],
        [295, 140, 72, 1.2, 17, 'C']
    ]

    # 이미지에서 추출한 테스트 포인트들
    test_points = [
        [300, 140, 60, 1.1, 18],
        [270, 125, 66, 0.95, 14],
        [310, 155, 53, 1.4, 23]
    ]

    k = 3 # K 설정

    print("=== 예측 결과 ===")
    for i, test_point in enumerate(test_points, 1):
        prediction = knn(train_data, test_point, k)
        print(f"Test Point {i} {test_point} : 카테고리 '{prediction}'")