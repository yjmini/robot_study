import math
from collections import Counter

# 두 데이터 포인트 사이의 유클리드 거리 계산
def euclidean_distance(point1, point2):
    distance = 0.0
    for i in range(len(point1)):
        distance += (point1[i] - point2[i]) ** 2
    return math.sqrt(distance)

# 주어진 데이터셋에서 새로운 데이터 포인트와 가장 가까운 K개의 이웃을 선택
def get_neighbors(train_data, test_point, k):
    distances = []
    for train_point in train_data:
        distance = euclidean_distance(test_point, train_point[:-1])  # 마지막 값은 라벨
        distances.append((train_point, distance))
    
    print("distances: ", distances)

    # 거리 순으로 정렬
    distances.sort(key=lambda x: x[1])  #입력값 x 가 주어졌을 때 x[1]을 반환
    
    print("sorted distances: ", distances)

    # 가장 가까운 k개의 이웃 반환
    neighbors = []
    for i in range(k):
        neighbors.append(distances[i][0])
    
    # print("neighbors: ", neighbors)
    return neighbors

# K개의 이웃 중 가장 많이 등장하는 클래스를 예측
def predict_classification(neighbors):
    output_values = [neighbor[-1] for neighbor in neighbors]  # 이웃들의 마지막 값(클래스)을 추출
    prediction = Counter(output_values).most_common(1)[0][0]  # 다수결 투표
    return prediction

# KNN 알고리즘 구현
def knn(train_data, test_point, k):
    neighbors = get_neighbors(train_data, test_point, k)  # k개의 가장 가까운 이웃 찾기
    prediction = predict_classification(neighbors)  # 예측
    return prediction

# 예시 데이터 및 테스트
if __name__ == '__main__':
    # 예시 데이터셋 (2D 데이터, 마지막 값이 클래스 라벨)
    train_data = [
        [2.7, 2.5, 'A'],
        [1.0, 1.0, 'B'],
        [3.0, 3.5, 'A'],
        [0.5, 1.0, 'B'],
        [2.8, 2.9, 'A'],
        [0.6, 0.7, 'B']
    ]

    # 테스트 데이터 포인트
    test_point = [1.5, 1.5]

    # K 값 설정
    k = 3

    # 예측 결과 출력
    prediction = knn(train_data, test_point, k)
    print(f'The predicted class for test point {test_point} is {prediction}')
