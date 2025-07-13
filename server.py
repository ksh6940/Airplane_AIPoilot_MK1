from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for
import os
import mapping  # 별도 모듈에 folium 지도 관리

app = Flask(__name__, template_folder='web')

# 메인 페이지
@app.route('/')
def index():
    return render_template('main.html', titles='항공네비')

# web 폴더 내 정적 파일 서빙 
@app.route('/web/<path:filename>')
def web_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web'), filename)

@app.route('/source/<path:filename>')
def source_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web', 'source'), filename)

# 지도 파일 리다이렉트
@app.route('/map.html')
def map_html():
    map_path = os.path.join(app.root_path, 'data', 'content', 'map.html')
    return send_from_directory(os.path.dirname(map_path), os.path.basename(map_path))

# 위치 데이터 받기 API
@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.get_json(force=True)
    place_name = data.get('place_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    print(f"받은 장소명: {place_name}, 위도: {latitude}, 경도: {longitude}")

    mapping.add_marker_and_save((latitude, longitude), name=place_name, address=data.get('address'))

    return jsonify({
        'success': True,
        'message': '지도 업데이트 완료',
        'reloadMap': True  
    })

@app.route('/api/map-action', methods=['POST'])
def map_action():
    data = request.get_json(force=True)
    action_type = data.get('type')
    print(f"📥 받은 데이터: {data}")

    # 지도 조작 관련 처리
    if action_type == 'changeMapType':
        map_type = data.get('mapType')
        print(f"지도 유형 변경 요청: {map_type}")
        mapping.change_map_type(map_type)
        return jsonify(success=True, message='지도 유형 변경', reloadMap=True)

    elif action_type == 'setZoom':
        zoom = data.get('zoomLevel')
        print(f"지도 줌 변경 요청: {zoom}")
        mapping.set_zoom(zoom)
        return jsonify(success=True, message='지도 줌 조정', reloadMap=True)

    elif action_type == 'markLocation':
        location = data.get('location')
        print(f"위치 마커 추가: {location}")
        mapping.add_marker_and_save(location)
        return jsonify(success=True, message='위치 마커 추가됨', reloadMap=True)

    # UI 상태 관련 처리
    elif action_type == 'uiState':
        sidebar = data.get('sidebarOpen')
        mode = data.get('activeMode')
        print(f"📋 UI 상태: 사이드바 열림 여부: {sidebar}, 모드: {mode}")
        return jsonify(success=True)

    elif action_type == 'buttonEvent':
        button = data.get('button')
        value = data.get('value')
        print(f"🔘 버튼 클릭: {button}, 입력값: {value}")
        return jsonify(success=True)

    elif action_type == 'filterConfirm':
        selected_filters = data.get('selectedFilters')
        print(f"🎯 필터 확정: {selected_filters}")
        mapping.set_filter(selected_filters)
        return jsonify(success=True, message='필터 적용 완료', reloadMap=True)


    # 알 수 없는 타입 처리
    else:
        print("⚠️ 알 수 없는 액션 타입")
        return jsonify(success=False, message='알 수 없는 요청 타입'), 400


if __name__ == '__main__':
    app.run(debug=True)
