from queue import PriorityQueue
import math

def haversine_distance(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371  # 지구 반지름 (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    aa = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(aa), math.sqrt(1-aa))

# 목표 지점 근접 여부 판단 함수 (20m 이내 허용)
def is_goal(current, end, threshold_m=20):
    dist_km = haversine_distance(current, end)
    return dist_km * 1000 <= threshold_m  # m 단위 변환 후 비교

def get_route(start, end):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    
    while not open_set.empty():
        _, current = open_set.get()
        
        # 도착 조건: 일정 거리 이내 도달하면 성공
        if is_goal(current, end):
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path
        
        step = 0.0005  # 노드 간격 (약 50m 내외)

        for dx in [-step, 0, step]:
            for dy in [-step, 0, step]:
                if dx == 0 and dy == 0:
                    continue
                neighbor = (round(current[0] + dx, 6), round(current[1] + dy, 6))
                
                tentative_g = g_score[current] + haversine_distance(current, neighbor)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    priority = tentative_g + haversine_distance(neighbor, end)
                    open_set.put((priority, neighbor))
                    came_from[neighbor] = current
                    
    return None  # 경로 없음

def calculate_path_length(path):
    if not path or len(path) < 2:
        return 0.0
    total_distance = 0.0
    for i in range(len(path)-1):
        total_distance += haversine_distance(path[i], path[i+1])
    return total_distance  # 단위: km

def estimate_travel_time(distance_km, speed_kmh=50):
    hours = distance_km / speed_kmh
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    if h > 0:
        return f"{h}시간 {m}분"
    else:
        return f"{m}분"
        