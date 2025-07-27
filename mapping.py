import pandas as pd
import folium
import re
import os
import navigation

# 경로 설정
content_dir = os.path.join(os.getcwd(), 'data', 'content')
map_path = os.path.join(os.getcwd(), 'web', 'map.html')
icon_path = 'web/source/marker.png'
marker_icon = folium.CustomIcon(icon_path, icon_size=(32, 32))

# 전역 변수
default_location = [37.55467884, 126.9706069]
default_zoom = 12

type_color = {
    '초경량비행장치 비행공역': 'green',
    '비행금지구역': 'red',
    '비행 제한 구역': 'orange',
    'ALERT 구역': 'purple',
    '비행 위험 구역': 'blue',
    '군작전 공역': 'gray',
}

filter_to_type_map = {
    '비행 금지': '비행금지구역',
    '비행 제한': '비행 제한 구역',
    '비행 경고': 'ALERT 구역',
    '비행 위험': '비행 위험 구역',
    '군 작전': '군작전 공역',
    '비행 가능': '초경량비행장치 비행공역',
}

# 모든 '비행 금지' 또는 '비행 제한' 관련 공역 유형 목록
# 이 목록은 필터 설정과 관계없이 항상 적용됩니다.
FORBIDDEN_AIRSPACE_TYPES = [
    '비행금지구역',
    '비행 제한 구역',
    'ALERT 구역',
    '비행 위험 구역',
    '군작전 공역'
]

# 필터 기본값: 모든 키 넣음
initial_filter_types = list(filter_to_type_map.keys())

map_state = {
    'zoom': default_zoom,
    'map_type': 'normal',
    'filter_types': initial_filter_types,
    'location': default_location,
    'markers': [],
    'route': []
}

def get_state():
    return map_state

# DMS 좌표 → 십진수 변환 함수
def dms_to_decimal(dms):
    match = re.match(r'(\d{2,3})(\d{2})(\d{2})([NSWE])', dms)
    if not match:
        return None
    deg, minute, sec, direction = match.groups()
    decimal = int(deg) + int(minute)/60 + int(sec)/3600
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

# 폴리곤 좌표 파싱 함수
def parse_polygon_pos(pos_str):
    coord_pattern = r'(\d{6}[NS])\s*(\d{7}[EW])'
    matches = re.findall(coord_pattern, pos_str.replace('-', ''))
    coords = [[dms_to_decimal(lat), dms_to_decimal(lon)] for lat, lon in matches]
    return [c for c in coords if None not in c]

# 기본 지도 생성 함수
def create_base_map():
    tiles = 'OpenStreetMap'
    attr = None
    if map_state['map_type'] == 'satellite':
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        attr = 'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics'

    m = folium.Map(
        location=map_state['location'],
        zoom_start=map_state['zoom'],
        tiles=None,
        zoom_control=False
    )
    folium.TileLayer(tiles=tiles, attr=attr, overlay=False, control=False).add_to(m)

    # 필터링된 공역만 그립니다.
    if map_state['filter_types']:
        standard_types = [filter_to_type_map.get(ft.strip()) for ft in map_state['filter_types']]
        standard_types = [t for t in standard_types if t]
        df_draw = df_polygons[df_polygons['type'].isin(standard_types)]
    else:
        df_draw = pd.DataFrame(columns=df_polygons.columns) # 필터가 없으면 아무것도 그리지 않습니다.

    for _, row in df_draw.iterrows():
        coords = parse_polygon_pos(row['pos'])
        if len(coords) >= 3:
            t = row['type']
            tooltip_html = f"<b>{t}</b><br>{row['name']}<br><span style='color:#888'>{row['height']}</span>"
            folium.Polygon(
                locations=coords,
                color=type_color.get(t, 'blue'),
                fill=True, fill_opacity=0.25, weight=3,
                dash_array='5, 5',
                popup=tooltip_html,
                tooltip=tooltip_html
            ).add_to(m)

    # 마커 추가 (기본 마커 + popup + tooltip)
    for lat, lon, popup, tooltip in map_state['markers']:
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=tooltip,
            icon=marker_icon
        ).add_to(m)

    return m

# 특정 위치가 금지 공역 내에 있는지 확인하는 함수 (Bounding Box 기반)
def is_location_forbidden(lat, lon):
    forbidden_zones = [] # 위치가 속한 금지 공역 목록
    for _, row in df_polygons.iterrows():
        # 해당 공역 유형이 금지 공역 목록에 있는지 확인
        if row['type'] in FORBIDDEN_AIRSPACE_TYPES:
            coords = parse_polygon_pos(row['pos'])
            if len(coords) >= 3:
                # Bounding Box (경계 상자) 기반의 대략적인 검사
                # 실제 Point-in-Polygon 검사를 위해서는 shapely 라이브러리 사용을 추천합니다.
                min_lat = min(c[0] for c in coords)
                max_lat = max(c[0] for c in coords)
                min_lon = min(c[1] for c in coords)
                max_lon = max(c[1] for c in coords)

                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    forbidden_zones.append(f"{row['name']} ({row['type']})")

    if forbidden_zones:
        return True, forbidden_zones
    return False, []


# 마커 추가 및 저장 함수
def add_marker_and_save(location, name=None, address=None):
    lat, lon = location

    is_forbidden, forbidden_details = is_location_forbidden(lat, lon)
    status = "🔴 비행 금지" if is_forbidden else "🟢 비행 가능"
    status_color = "red" if is_forbidden else "green"

    forbidden_info = ""
    if is_forbidden:
        forbidden_info = "<p style='margin:4px 0; font-size:13px; color:#c00;'><b><br>영향 공역:</b></p>"
        for zone in forbidden_details:
            forbidden_info += f"<p style='margin:2px 0; font-size:12px; color:#c00;'>- {zone}</p>"

    popup_html = f"""
    <div style="font-family: 'SeoulAlrimTTF-Heavy', sans-serif; padding:15px; width:280px; color:#333; background-color:#ffffff; border-radius:8px;">
        <h4 style="margin:0 0 10px 0; font-size:18px; color:#000;">📍 {name or "이름 없음"}</h4>
        <p style="margin:5px 0; font-size:14px;"><b>주소:</b> {address or "주소 없음"}</p>
        <p style="margin:5px 0; font-size:14px;"><b>위치:</b> {lat:.6f}, {lon:.6f}</p>
        <p style="margin:8px 0 5px 0; font-size:15px; font-weight:bold; color:{status_color};">
            비행 가능 여부: {status}
        </p>
        {forbidden_info}
    </div>
    """

    map_state['markers'].append([lat, lon, popup_html, name or "마커"])
    map_state['location'] = [lat, lon]

    m = create_base_map()
    m.save(map_path)
    print(f"✅ 마커 추가 및 저장 완료: {map_path}")


# 지도 유형 변경
def change_map_type(new_type):
    map_state['map_type'] = new_type
    m = create_base_map()
    m.save(map_path)
    print(f"✅ 지도 유형 변경 완료: {map_path}")

# 줌 레벨 변경
def set_zoom(zoom):
    map_state['zoom'] = zoom
    m = create_base_map()
    m.save(map_path)
    print(f"✅ 줌 레벨 변경 완료: {map_path}")

# 필터 설정 및 저장
def set_filter(filter_types):
    map_state['filter_types'] = filter_types
    m = create_base_map()
    m.save(map_path)
    print(f"✅ 필터 적용 완료: {map_path}")

def clear_all_markers():
    print("💣 모든 마커 초기화 중...")
    map_state['markers'] = []
    m = create_base_map()
    m.save(map_path)
    print("✅ 마커 초기화 및 저장 완료")

def clear_route():
    print("💣 경로 초기화 중...")
    map_state['route'] = []
    map_state['markers'] = []
    m = create_base_map()
    m.save(map_path)
    print("✅ 경로 초기화 및 저장 완료")

# 두 지점 간의 거리를 기반으로 줌 레벨을 계산하는 함수 (Haversine 공식 근사치)
def get_zoom_level(lat1, lon1, lat2, lon2):
    # 위도 및 경도 차이 계산
    delta_lat = abs(lat1 - lat2)
    delta_lon = abs(lon1 - lon2)

    # 대략적인 지도 줌 레벨 매핑 (경험적 값)
    # 이 값들은 테스트를 통해 최적화할 수 있습니다.
    max_delta = max(delta_lat, delta_lon)

    if max_delta < 0.005:  # 약 500m 이내
        return 17
    elif max_delta < 0.01: # 약 1km 이내
        return 16
    elif max_delta < 0.02: # 약 2km 이내
        return 15
    elif max_delta < 0.05: # 약 5km 이내
        return 14
    elif max_delta < 0.1:  # 약 10km 이내
        return 13
    elif max_delta < 0.2:  # 약 20km 이내
        return 12
    elif max_delta < 0.5:  # 약 50km 이내
        return 10
    elif max_delta < 1.0:  # 약 100km 이내
        return 9
    else: # 그 이상
        return 8

def add_route(start_location, end_location, place_names):
    map_state['markers'] = []
    start_place_name, end_place_name = place_names

    start_lat, start_lon = start_location
    end_lat, end_lon = end_location

    # 금지구역 체크 제외, 단순 A* 탐색
    path = navigation.get_route(start_location, end_location)

    if path and isinstance(path[0], tuple):
        path = [[lat, lon] for lat, lon in path]  # 좌표 순서가 (lat, lon)로 정리

    print("🚧 A* 경로:", path)
    if not path:
        print("❌ A* 탐색 실패: 경로 없음")

    distance = navigation.calculate_path_length(path) if path else None
    travel_time = navigation.estimate_travel_time(distance) if distance is not None else None

    # 경로 분석: 경로가 금지구역을 지나면 일괄 주의 메시지
    alerts = []
    if path:
        for point in path:
            is_forbidden, forbidden_details = is_location_forbidden(point[0], point[1])
            if is_forbidden:
                for zone in forbidden_details:
                    if zone not in alerts:
                        alerts.append(zone)

    # 팝업 생성: distance, travel_time, 경로 분석 결과 포함
    analysis_html = ""
    if alerts:
        analysis_html = "<div style='margin-top:8px; color:#c00; font-size:13px;'><b>경로 분석:</b><ul style='margin:4px 0 0 12px; padding:0;'>"
        analysis_html += "<li>경로가 지도 내 비행 금지/제한/경고/군작전 구역을 지나갑니다. 경로를 수정하거나 해당 구역에 주의하세요.</li>"
        analysis_html += "</ul></div>"

    start_popup = f"""
    <div style="font-family: 'SeoulAlrimTTF-Heavy', sans-serif; padding:15px; width:280px; color:#333;">
        <h4 style="margin:0 0 10px 0; font-size:18px; color:#1e90ff;">🛫 출발지</h4>
        <p style="margin:5px 0; font-size:14px;"><b>장소명:</b> {start_place_name}</p>
        <p style="margin:5px 0; font-size:14px;"><b>위치:</b> {start_lat:.6f}, {start_lon:.6f}</p>
    </div>
    """

    end_popup = f"""
    <div style="font-family: 'SeoulAlrimTTF-Heavy', sans-serif; padding:15px; width:280px; color:#333;">
        <h4 style="margin:0 0 10px 0; font-size:18px; color:#800080;">🛬 도착지</h4>
        <p style="margin:5px 0; font-size:14px;"><b>장소명:</b> {end_place_name}</p>
        <p style="margin:5px 0; font-size:14px;"><b>위치:</b> {end_lat:.6f}, {end_lon:.6f}</p>
        {f"<p style='margin:5px 0; font-size:14px;'><b>거리:</b> {distance:.2f} km</p>" if distance is not None else ""}
        {f"<p style='margin:5px 0; font-size:14px;'><b>예상 시간:</b> {travel_time}</p>" if travel_time is not None else ""}
        {analysis_html}
    </div>
    """

    map_state['markers'].append([start_lat, start_lon, start_popup, "출발지"])
    map_state['markers'].append([end_lat, end_lon, end_popup, "도착지"])

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    map_state['location'] = [center_lat, center_lon]
    map_state['zoom'] = get_zoom_level(start_lat, start_lon, end_lat, end_lon)
    map_state['route'] = path if path else []

    m = create_base_map()

    if path:
        folium.PolyLine(locations=path, color='green', weight=5, opacity=0.7).add_to(m)
    else:
        print("⚠️ 경로를 찾을 수 없습니다. 노드 밀도 또는 범위 부족일 수 있습니다.")

    m.save(map_path)
    print("✅ 경로 마커 및 지도 저장 완료")

    return {
        "start_point": start_place_name,
        "end_point": end_place_name,
        "estimated_time": travel_time,
        "total_distance": f"{distance:.2f} km" if distance is not None else "N/A",
        "analysis": {
            "warnings": ["경로가 지도 내 비행 금지/제한/경고/군작전 구역을 지나갑니다. 경로를 수정하거나 해당 구역에 주의하세요."] if alerts else []
        },
        "analysis_html": analysis_html
    }

# 공역 좌표 데이터 로드
df = pd.read_csv(os.path.join(content_dir, 'airspace_data.csv'))
df_polygons = df[~df['pos'].str.contains('반경', na=False)].copy()

# 최초 기본 지도 저장
base_map = create_base_map()
base_map.save(map_path)
print(f"✅ 기본 지도 생성 완료: {map_path}")