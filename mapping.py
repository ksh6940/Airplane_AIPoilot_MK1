import pandas as pd
import folium
import re
import os

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

# 필터 기본값: 모든 키 넣음
initial_filter_types = list(filter_to_type_map.keys())

map_state = {
    'zoom': default_zoom,
    'map_type': 'normal',
    'filter_types': initial_filter_types,
    'location': default_location,
    'markers': []
}

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

    if map_state['filter_types']:
        standard_types = [filter_to_type_map.get(ft.strip()) for ft in map_state['filter_types']]
        standard_types = [t for t in standard_types if t]
        df_draw = df_polygons[df_polygons['type'].isin(standard_types)]
    else:
        df_draw = pd.DataFrame(columns=df_polygons.columns)  

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

# 마커 추가 및 저장 함수
def add_marker_and_save(location, name=None, address=None):
    lat, lon = location

    # 마커 ID 및 상태 판별
    index = len(map_state['markers'])
    flight_allowed = not any(
        filter_to_type_map.get(ft.strip()) in {
            '비행금지구역', '비행 제한 구역', 'ALERT 구역', '비행 위험 구역', '군작전 공역'
        }
        for ft in map_state['filter_types']
    )
    status = "🟢 가능" if flight_allowed else "🔴 금지"

    # 깔끔한 팝업 HTML
    popup_html = f"""
    <div style="font-family:sans-serif; padding:12px; width:250px; color:#333;">
        <h4 style="margin:0 0 8px 0; font-size:16px;">📍 {name or "이름 없음"}</h4>
        <p style="margin:4px 0; font-size:14px;"><b>주소:</b> {address or "주소 없음"}</p>
        <p style="margin:4px 0; font-size:14px;"><b>위치:</b> {lat:.6f}, {lon:.6f}</p>
        <p style="margin:4px 0; font-size:14px;"><b>비행:</b> <span style="font-weight:bold;">{status}</span></p>
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

# 공역 좌표 데이터 로드
df = pd.read_csv(os.path.join(content_dir, 'airspace_data.csv'))
df_polygons = df[~df['pos'].str.contains('반경', na=False)].copy()

# 최초 기본 지도 저장
base_map = create_base_map()
base_map.save(map_path)
print(f"✅ 기본 지도 생성 완료: {map_path}")
