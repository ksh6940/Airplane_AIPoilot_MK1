# app.py - Main Flask Application

from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import mapping  # Assuming 'mapping.py' exists and manages Folium map operations

app = Flask(__name__, template_folder='web')

# Main page route
@app.route('/')
def index():
    return render_template('main.html', titles='항공네비')

# Serve static files from the 'web' folder
@app.route('/web/<path:filename>')
def web_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web'), filename)

# Serve static files from the 'web/source' folder
@app.route('/source/<path:filename>')
def source_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'web', 'source'), filename)

# Redirect to the map HTML file
@app.route('/map.html')
def map_html():
    map_path = os.path.join(app.root_path, 'data', 'content', 'map.html')
    return send_from_directory(os.path.dirname(map_path), os.path.basename(map_path))

# API to receive location data and add a marker
@app.route('/api/location', methods=['POST'])
def receive_location():
    data = request.get_json(silent=True)  # Returns None on failure instead of error
    if not data:
        return jsonify(success=False, message='Bad request: JSON format required'), 400

    place_name = data.get('place_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is None or longitude is None:
        return jsonify(success=False, message='Latitude and longitude values are required'), 400

    mapping.add_marker_and_save((latitude, longitude), name=place_name, address=data.get('address'))
    return jsonify({
        'success': True,
        'message': f'Location marker added: {place_name or f"{latitude}, {longitude}"}',
        'reloadMap': True
    })

# API for map actions (change map type, zoom, add marker, UI state, filters)
@app.route('/api/map-action', methods=['POST'])
def map_action():
    data = request.get_json(force=True)
    action_type = data.get('type')
    print(f"📥 Received data: {data}")

    if action_type == 'changeMapType':
        map_type = data.get('mapType')
        print(f"Map type change request: {map_type}")
        mapping.change_map_type(map_type)
        return jsonify(success=True, message='Map type changed', reloadMap=True)

    elif action_type == 'setZoom':
        zoom = data.get('zoomLevel')
        print(f"Map zoom change request: {zoom}")
        mapping.set_zoom(zoom)
        return jsonify(success=True, message='Map zoom adjusted', reloadMap=True)

    elif action_type == 'markLocation':
        location = data.get('location')
        print(f"Adding location marker: {location}")
        mapping.add_marker_and_save(location)
        return jsonify(success=True, message='Location marker added', reloadMap=True)

    elif action_type == 'uiState':
        sidebar = data.get('sidebarOpen')
        mode = data.get('activeMode')
        print(f"📋 UI State: Sidebar open: {sidebar}, Mode: {mode}")
        return jsonify(success=True)

    elif action_type == 'buttonEvent':
        button = data.get('button')
        value = data.get('value')
        print(f"🔘 Button clicked: {button}, Input value: {value}")
        return jsonify(success=True)

    elif action_type == 'filterConfirm':
        selected_filters = data.get('selectedFilters')
        print(f"🎯 Filter confirmed: {selected_filters}")
        mapping.set_filter(selected_filters)
        return jsonify(success=True, message='Filters applied', reloadMap=True)
        
    elif action_type == 'markerAdded':
        location = data.get('payload')
        print(f"Adding location marker (markerAdded): {location}")
        if location:
            mapping.add_marker_and_save(location)
            return jsonify(success=True, message='Location marker added', reloadMap=True)
        else:
            return jsonify(success=False, message='No location data provided'), 400
    else:
        print("⚠️ Unknown action type")
        return jsonify(success=False, message='Unknown request type'), 400

# API to delete all markers
@app.route('/api/deleteMarker', methods=['POST'])
def delete_marker():
    try:
        print("🧹 Marker deletion request received")
        mapping.clear_all_markers()  # This function needs to be implemented in mapping.py
        return jsonify(success=True, message='All markers removed', reloadMap=True)
    except Exception as e:
        print(f"❌ Marker deletion error: {e}")
        return jsonify(success=False, message=f'Failed to remove markers: {e}'), 500

# **새로 추가할 /api/route 엔드포인트**
@app.route('/api/route', methods=['POST'])
def handle_route():
    try:
        data = request.json
        print(f"Received route data: {data}")

        start_lat, start_lon = data['startLocation']['latitude'], data['startLocation']['longitude']
        end_lat, end_lon = data['endLocation']['latitude'], data['endLocation']['longitude']
        start_name, end_name = data['startLocation']['name'].split(',')[0].strip(), data['endLocation']['name'].split(',')[0].strip()

        mapping.add_route((start_lat, start_lon), (end_lat, end_lon), (start_name, end_name))

        return jsonify({"success": True, "message": "경로 데이터가 성공적으로 서버에 전송되었습니다."})

    except Exception as e:
        print(f"Error in /api/route: {e}")
        return jsonify({"success": False, "message": f"서버 처리 중 오류 발생: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')