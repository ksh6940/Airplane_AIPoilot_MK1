# navigation.py
from queue import PriorityQueue
import math
from shapely.geometry import Point, Polygon

def is_blocked(point, forbidden_polygons):
    """
    point: (lat, lon) 튜플
    forbidden_polygons: 폴리곤 리스트 (각각은 [(lat1, lon1), (lat2, lon2), ...])
    
    점이 금지 구역(폴리곤) 안에 있으면 True 반환
    """
    p = Point(point[0], point[1])
    for poly_coords in forbidden_polygons:
        poly = Polygon(poly_coords)
        if poly.contains(p):
            return True
    return False


def haversine_distance(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371  # 지구 반지름 (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_in_polygon(point, polygon):
    return Polygon(polygon).contains(Point(point))

def is_blocked(point, forbidden_polygons):
    for poly in forbidden_polygons:
        if is_in_polygon(point, poly):
            return True
    return False

def astar(start, end, forbidden_polygons, is_blocked_func):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    
    while not open_set.empty():
        _, current = open_set.get()
        
        if current == end:
            # 경로 복원
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path
        
        # 8방향 인접 노드 탐색 (0.001도 단위 - 약 100m 근접)
        for dx in [-0.001, 0, 0.001]:
            for dy in [-0.001, 0, 0.001]:
                if dx == 0 and dy == 0:
                    continue
                neighbor = (round(current[0] + dx, 6), round(current[1] + dy, 6))
                if is_blocked_func(neighbor, forbidden_polygons):
                    continue
                
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
