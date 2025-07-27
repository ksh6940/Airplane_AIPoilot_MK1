from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import mapping
import time
import requests
import threading
from collections import OrderedDict
import json

app = Flask(__name__, template_folder='web')

last_request_time = 0
REQUEST_INTERVAL = 1.1  # seconds
last_request_lock = threading.Lock()  # 스레드 동기화용 락

# 간단 LRU 캐시 (최대 100개 저장)
class LRUCache:
    def __init__(self, capacity=100):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

cache = LRUCache()

@app.route('/')
def index():
    try:
        global map_state
        map_state = mapping.get_state()

        print("📡 map_state =", map_state)  # 콘솔 확인
        print("📡 타입 =", {k: type(v) for k, v in map_state.items()})

    except Exception as e:
        print("🛑 오류 발생:", e)
        map_state = {}

    return render_template("main.html", map_state_json=map_state)

@app.route('/web/<path:filename>')
def web_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web'), filename)

@app.route('/source/<path:filename>')
def source_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web', 'source'), filename)

@app.route('/map.html')
def map_html():
    map_path = os.path.join(app.root_path, 'data', 'content', 'map.html')
    return send_from_directory(os.path.dirname(map_path), os.path.basename(map_path))

@app.route('/api/location', methods=['POST'])
def receive_location():
    # 위치 검색 시 기존 마커 초기화 (경로검색 마커와 병존 방지)
    mapping.clear_all_markers()

    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message='Bad request: JSON 형식 필요'), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    place_name = data.get('place_name')

    if latitude is None or longitude is None:
        return jsonify(success=False, message='위도와 경도 값이 필요합니다'), 400

    try:
        mapping.add_marker_and_save((latitude, longitude), name=place_name, address=data.get('address'))
    except Exception as e:
        return jsonify(success=False, message=f'마커 추가 실패: {e}'), 500

    return jsonify({
        'success': True,
        'message': f'위치 마커 추가됨: {place_name or f"{latitude}, {longitude}"}',
        'reloadMap': True
    })

@app.route('/api/map-action', methods=['POST'])
def map_action():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="잘못된 JSON 데이터"), 400

    action_type = data.get('type')
    print(f"📥 받은 데이터: {data}")

    try:
        if action_type == 'changeMapType':
            map_type = data.get('mapType')
            print(f"지도 유형 변경 요청: {map_type}")
            mapping.change_map_type(map_type)
            return jsonify(success=True, message='지도 유형 변경됨', reloadMap=True)

        elif action_type == 'setZoom':
            zoom = data.get('zoomLevel')
            print(f"지도 줌 레벨 변경 요청: {zoom}")
            mapping.set_zoom(zoom)
            return jsonify(success=True, message='지도 줌 변경됨', reloadMap=True)

        elif action_type == 'markLocation':
            location = data.get('location')
            print(f"위치 마커 추가 요청: {location}")
            mapping.add_marker_and_save(location)
            return jsonify(success=True, message='위치 마커 추가됨', reloadMap=True)

        elif action_type == 'uiState':
            sidebar = data.get('sidebarOpen')
            mode = data.get('activeMode')
            print(f"📋 UI 상태: 사이드바 열림={sidebar}, 모드={mode}")
            return jsonify(success=True)

        elif action_type == 'buttonEvent':
            button = data.get('button')
            value = data.get('value')
            print(f"🔘 버튼 클릭: {button}, 값: {value}")
            return jsonify(success=True)

        elif action_type == 'filterConfirm':
            selected_filters = data.get('selectedFilters')
            print(f"🎯 필터 적용: {selected_filters}")
            mapping.set_filter(selected_filters)
            return jsonify(success=True, message='필터 적용됨', reloadMap=True)

        elif action_type == 'markerAdded':
            location = data.get('payload')
            print(f"마커 추가 (markerAdded): {location}")
            if location:
                mapping.add_marker_and_save(location)
                return jsonify(success=True, message='마커 추가됨', reloadMap=True)
            else:
                return jsonify(success=False, message='위치 데이터가 없습니다'), 400

        else:
            print("⚠️ 알 수 없는 요청 타입")
            return jsonify(success=False, message='알 수 없는 요청 타입'), 400

    except Exception as e:
        print(f"❌ map-action 처리 중 오류: {e}")
        return jsonify(success=False, message=f'오류 발생: {e}'), 500

@app.route('/api/deleteMarker', methods=['POST'])
def delete_marker():
    try:
        print("🧹 마커 삭제 요청")
        mapping.clear_all_markers()
        return jsonify(success=True, message='모든 마커 삭제됨', reloadMap=True)
    except Exception as e:
        print(f"❌ 마커 삭제 오류: {e}")
        return jsonify(success=False, message=f'마커 삭제 실패: {e}'), 500

@app.route('/api/delete-route', methods=['POST'])
def delete_route():
    try:
        print("🧹 경로 삭제 요청")
        mapping.clear_route()
        return jsonify(success=True, message='경로 삭제됨', reloadMap=True)
    except Exception as e:
        print(f"❌ 경로 삭제 오류: {e}")
        return jsonify(success=False, message=f'경로 삭제 실패: {e}'), 500

@app.route('/api/route', methods=['POST'])
def handle_route():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify(success=False, message="JSON 데이터 필요"), 400

        # 경로 검색 시 기존 위치검색 마커 초기화 (병존 방지)
        mapping.clear_all_markers()

        start_loc = data.get('startLocation')
        end_loc = data.get('endLocation')
        if not start_loc or not end_loc:
            return jsonify(success=False, message="출발지 또는 도착지 정보 누락"), 400

        try:
            start_lat = float(start_loc.get('latitude'))
            start_lon = float(start_loc.get('longitude'))
            end_lat = float(end_loc.get('latitude'))
            end_lon = float(end_loc.get('longitude'))
        except (TypeError, ValueError):
            return jsonify(success=False, message="위도/경도는 숫자여야 함"), 400

        start_name = start_loc.get('name', '').split(',')[0].strip()
        end_name = end_loc.get('name', '').split(',')[0].strip()

        # mapping.add_route()는 경로 계산, 지도 시각화, 예상시간/거리 계산, 필터 경고 분석 후 dict 리턴
        route_info = mapping.add_route(
            (start_lat, start_lon),
            (end_lat, end_lon),
            (start_name, end_name)
        )

        return jsonify({
            "success": True,
            "message": "경로가 성공적으로 처리됨",
            "summary": route_info,
            "analysis": route_info["analysis"]
        })

    except Exception as e:
        print(f"/api/route 처리 중 오류: {e}")
        return jsonify({"success": False, "message": f"서버 오류: {str(e)}"}), 500

@app.route("/api/geocode")
def geocode():
    global last_request_time

    address = request.args.get("q")
    if not address:
        return jsonify({"error": "주소가 필요합니다."}), 400

    cached_result = cache.get(address)
    if cached_result:
        return jsonify(cached_result)

    with last_request_lock:
        now = time.time()
        wait_time = REQUEST_INTERVAL - (now - last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "limit": 1,
            "q": address,
            "accept-language": "ko",
        }
        headers = {
            "User-Agent": "Airmap/1.0 (gsh6940@naver.com)",
            "Accept-Language": "ko",
        }

        response = requests.get(url, params=params, headers=headers)
        last_request_time = time.time()

    if response.status_code != 200:
        return jsonify({"error": f"HTTP 오류: {response.status_code}"}), 500

    data = response.json()
    if not data:
        return jsonify({"error": "주소를 찾을 수 없습니다."}), 404

    result = {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
        "display_name": data[0]["display_name"],
    }

    cache.set(address, result)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
