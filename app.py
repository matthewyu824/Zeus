from flask import Flask, render_template, request, jsonify
import threading
import json
import random
import time
from screen_operation import PointCollector, send_message

app = Flask(__name__)

collector = PointCollector()
collecting_thread = None
collecting_status = {"status": "idle", "type": "", "points": [], "message": "", "group_id": ""}

batch_control_status = {"status": "idle", "message": "", "category": "", "current_group": "", "sent_count": 0}
batch_control_thread = None
batch_control_running = False

def collect_common_points_background():
    global collecting_status
    collecting_status["status"] = "collecting"
    collecting_status["type"] = "common"
    collecting_status["points"] = []
    collecting_status["message"] = "开始收集公共点（点2、点3），请在屏幕上点击位置..."
    
    def on_click(x, y, button, pressed):
        if pressed and button.name == 'left':
            collecting_status["points"].append((x, y))
            collecting_status["message"] = f"已收集第 {len(collecting_status['points'])} 个公共点: ({x}, {y})"
            
            if len(collecting_status["points"]) >= 2:
                collecting_status["status"] = "completed"
                collecting_status["message"] = "公共点收集完成！"
                return False
    
    from pynput import mouse
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    
    if len(collecting_status["points"]) == 2:
        groups_data = collector.load_groups()
        if groups_data is None:
            groups_data = {"common_points": [], "group_points": {}}
        groups_data["common_points"] = collecting_status["points"]
        collector.save_groups(groups_data["common_points"], groups_data["group_points"])
        collecting_status["message"] = "公共点已保存到文件"
    else:
        collecting_status["status"] = "error"
        collecting_status["message"] = f"收集的点数量不足，需要2个点，实际收集了{len(collecting_status['points'])}个点"

def collect_group_points_background(group_id):
    global collecting_status
    collecting_status["status"] = "collecting"
    collecting_status["type"] = "group"
    collecting_status["group_id"] = group_id
    collecting_status["points"] = []
    collecting_status["message"] = f"开始收集组 {group_id} 的特定点（点1、点4、点5），请在屏幕上点击位置..."
    
    def on_click(x, y, button, pressed):
        if pressed and button.name == 'left':
            collecting_status["points"].append((x, y))
            collecting_status["message"] = f"已收集第 {len(collecting_status['points'])} 个特定点: ({x}, {y})"
            
            if len(collecting_status["points"]) >= 3:
                collecting_status["status"] = "completed"
                collecting_status["message"] = f"组 {group_id} 特定点收集完成！"
                return False
    
    from pynput import mouse
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    
    if len(collecting_status["points"]) == 3:
        groups_data = collector.load_groups()
        if groups_data is None:
            groups_data = {"common_points": [], "group_points": {}}
        groups_data["group_points"][group_id] = collecting_status["points"]
        collector.save_groups(groups_data["common_points"], groups_data["group_points"])
        collecting_status["message"] = f"组 {group_id} 特定点已保存到文件"
    else:
        collecting_status["status"] = "error"
        collecting_status["message"] = f"收集的点数量不足，需要3个点，实际收集了{len(collecting_status['points'])}个点"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(collecting_status)

@app.route('/api/collect/common', methods=['POST'])
def start_collect_common():
    global collecting_thread
    
    if collecting_status["status"] == "collecting":
        return jsonify({"success": False, "message": "正在收集坐标点，请稍候..."})
    
    collecting_thread = threading.Thread(target=collect_common_points_background)
    collecting_thread.start()
    
    return jsonify({"success": True, "message": "开始收集公共点"})

@app.route('/api/collect/group', methods=['POST'])
def start_collect_group():
    global collecting_thread
    
    if collecting_status["status"] == "collecting":
        return jsonify({"success": False, "message": "正在收集坐标点，请稍候..."})
    
    data = request.json
    group_id = data.get('group_id', '')
    
    if not group_id:
        return jsonify({"success": False, "message": "组ID不能为空"})
    
    collecting_thread = threading.Thread(target=collect_group_points_background, args=(group_id,))
    collecting_thread.start()
    
    return jsonify({"success": True, "message": f"开始收集组 {group_id} 的特定点"})

@app.route('/api/send', methods=['POST'])
def send_message_api():
    data = request.json
    message = data.get('message', '')
    group_id = data.get('group_id', '')
    
    if not message:
        return jsonify({"success": False, "message": "消息不能为空"})
    
    if not group_id:
        return jsonify({"success": False, "message": "组ID不能为空"})
    
    try:
        send_message(message, group_id)
        return jsonify({"success": True, "message": "消息发送成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/groups', methods=['GET'])
def get_groups():
    groups_data = collector.load_groups()
    if groups_data:
        return jsonify({"success": True, "data": groups_data})
    return jsonify({"success": False, "message": "无法读取组数据文件"})

@app.route('/api/groups/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    groups_data = collector.load_groups()
    if groups_data is None:
        return jsonify({"success": False, "message": "无法读取组数据文件"})
    
    if group_id not in groups_data["group_points"]:
        return jsonify({"success": False, "message": f"组 {group_id} 不存在"})
    
    del groups_data["group_points"][group_id]
    collector.save_groups(groups_data["common_points"], groups_data["group_points"])
    
    return jsonify({"success": True, "message": f"组 {group_id} 已删除"})

@app.route('/api/scripts/categories', methods=['GET'])
def get_script_categories():
    try:
        with open('话术.json', 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        categories = list(scripts.keys())
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch/start', methods=['POST'])
def start_batch_control():
    global batch_control_thread, batch_control_running
    
    if batch_control_running:
        return jsonify({"success": False, "message": "群控正在运行中"})
    
    data = request.json
    category = data.get('category', '')
    
    if not category:
        return jsonify({"success": False, "message": "话术类别不能为空"})
    
    try:
        with open('话术.json', 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category not in scripts:
            return jsonify({"success": False, "message": f"话术类别 {category} 不存在"})
        
        batch_control_running = True
        batch_control_thread = threading.Thread(target=batch_control_worker, args=(category,))
        batch_control_thread.start()
        
        return jsonify({"success": True, "message": f"开始群控，话术类别：{category}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch/stop', methods=['POST'])
def stop_batch_control():
    global batch_control_running
    
    if not batch_control_running:
        return jsonify({"success": False, "message": "群控未在运行"})
    
    batch_control_running = False
    return jsonify({"success": True, "message": "群控已停止"})

@app.route('/api/batch/status', methods=['GET'])
def get_batch_status():
    return jsonify(batch_control_status)

def batch_control_worker(category):
    global batch_control_status, batch_control_running
    
    try:
        with open('话术.json', 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        messages = scripts.get(category, [])
        if not messages:
            batch_control_status["status"] = "error"
            batch_control_status["message"] = f"话术类别 {category} 没有可用消息"
            batch_control_running = False
            return
        
        groups_data = collector.load_groups()
        if groups_data is None:
            batch_control_status["status"] = "error"
            batch_control_status["message"] = "无法读取组数据文件"
            batch_control_running = False
            return
        
        group_ids = list(groups_data.get("group_points", {}).keys())
        if not group_ids:
            batch_control_status["status"] = "error"
            batch_control_status["message"] = "没有可用的组"
            batch_control_running = False
            return
        
        batch_control_status["status"] = "running"
        batch_control_status["category"] = category
        batch_control_status["sent_count"] = 0
        
        while batch_control_running:
            for group_id in group_ids:
                if not batch_control_running:
                    break
                
                message = random.choice(messages)
                batch_control_status["current_group"] = group_id
                batch_control_status["message"] = f"正在向组 {group_id} 发送消息：{message}"
                
                try:
                    send_message(message, group_id)
                    batch_control_status["sent_count"] += 1
                except Exception as e:
                    batch_control_status["message"] = f"发送失败：{str(e)}"
                
                time.sleep(1)
        
        batch_control_status["status"] = "idle"
        batch_control_status["message"] = "群控已停止"
        batch_control_running = False
        
    except Exception as e:
        batch_control_status["status"] = "error"
        batch_control_status["message"] = f"群控出错：{str(e)}"
        batch_control_running = False

if __name__ == '__main__':
    app.run(debug=True, port=5000)
