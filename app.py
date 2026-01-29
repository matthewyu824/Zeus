from flask import Flask, render_template, request, jsonify
import threading
import json
import random
import time
from pynput import keyboard
from screen_operation import PointCollector, send_message, send_message_all, enter_group_mode, exit_group_mode

app = Flask(__name__)

collector = PointCollector()
collecting_thread = None
collecting_status = {"status": "idle", "type": "", "points": [], "message": "", "group_id": ""}

batch_control_status = {"status": "idle", "message": "", "category": "", "current_group": "", "sent_count": 0}
batch_control_thread = None
batch_control_running = False

scheduled_send_status = {"status": "idle", "message": "", "group_id": "", "sent_count": 0, "next_send_time": None}
scheduled_send_thread = None
scheduled_send_running = False

global_keyboard_listener = None

def on_global_key_press(key):
    if key == keyboard.Key.esc:
        global batch_control_running, scheduled_send_running
        
        if batch_control_running:
            batch_control_running = False
            batch_control_status["status"] = "idle"
            batch_control_status["message"] = "已按ESC键停止群控"
        
        if scheduled_send_running:
            scheduled_send_running = False
            scheduled_send_status["status"] = "idle"
            scheduled_send_status["message"] = "已按ESC键停止定期发送"
            scheduled_send_status["next_send_time"] = None

def collect_common_points_background():
    global collecting_status
    collecting_status["status"] = "collecting"
    collecting_status["type"] = "common"
    collecting_status["points"] = []
    collecting_status["message"] = "开始收集公共点（4个点），请在屏幕上点击位置..."
    
    def on_click(x, y, button, pressed):
        if pressed and button.name == 'left':
            collecting_status["points"].append((x, y))
            collecting_status["message"] = f"已收集第 {len(collecting_status['points'])} 个公共点: ({x}, {y})"
            
            if len(collecting_status["points"]) >= 4:
                collecting_status["status"] = "completed"
                collecting_status["message"] = "公共点收集完成！"
                return False
    
    from pynput import mouse
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    
    if len(collecting_status["points"]) == 4:
        groups_data = collector.load_groups()
        if groups_data is None:
            groups_data = {"common_points": [], "group_points": {}}
        groups_data["common_points"] = collecting_status["points"]
        collector.save_groups(groups_data["common_points"], groups_data["group_points"])
        collecting_status["message"] = "公共点已保存到文件"
    else:
        collecting_status["status"] = "error"
        collecting_status["message"] = f"收集的点数量不足，需要4个点，实际收集了{len(collecting_status['points'])}个点"

def collect_group_points_background(group_id):
    global collecting_status
    collecting_status["status"] = "collecting"
    collecting_status["type"] = "group"
    collecting_status["group_id"] = group_id
    collecting_status["points"] = []
    collecting_status["message"] = f"开始收集设备 {group_id} 的特定点（点1、点4、点5），请在屏幕上点击位置..."
    
    def on_click(x, y, button, pressed):
        if pressed and button.name == 'left':
            collecting_status["points"].append((x, y))
            collecting_status["message"] = f"已收集第 {len(collecting_status['points'])} 个特定点: ({x}, {y})"
            
            if len(collecting_status["points"]) >= 3:
                collecting_status["status"] = "completed"
                collecting_status["message"] = f"设备 {group_id} 特定点收集完成！"
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
        collecting_status["message"] = f"设备 {group_id} 特定点已保存到文件"
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
        return jsonify({"success": False, "message": "设备ID不能为空"})
    
    collecting_thread = threading.Thread(target=collect_group_points_background, args=(group_id,))
    collecting_thread.start()
    
    return jsonify({"success": True, "message": f"开始收集设备 {group_id} 的特定点"})

@app.route('/api/send', methods=['POST'])
def send_message_api():
    data = request.json
    message = data.get('message', '')
    group_id = data.get('group_id', '')
    speed = data.get('speed', '中')
    
    if not message:
        return jsonify({"success": False, "message": "消息不能为空"})
    
    try:
        if not group_id or group_id == 'random':
            groups_data = collector.load_groups()
            if groups_data is None:
                return jsonify({"success": False, "message": "无法读取设备数据文件"})
            
            group_ids = list(groups_data.get("group_points", {}).keys())
            if not group_ids:
                return jsonify({"success": False, "message": "没有可用的设备"})
            
            target_group_id = random.choice(group_ids)
            send_message(message, target_group_id, speed)
            return jsonify({"success": True, "message": f"消息已发送到随机设备 {target_group_id}"})
        else:
            send_message(message, group_id, speed)
            return jsonify({"success": True, "message": "消息发送成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/groups', methods=['GET'])
def get_groups():
    groups_data = collector.load_groups()
    if groups_data:
        return jsonify({"success": True, "data": groups_data})
    return jsonify({"success": False, "message": "无法读取设备数据文件"})

@app.route('/api/groups/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    groups_data = collector.load_groups()
    if groups_data is None:
        return jsonify({"success": False, "message": "无法读取设备数据文件"})
    
    if group_id not in groups_data["group_points"]:
        return jsonify({"success": False, "message": f"设备 {group_id} 不存在"})
    
    del groups_data["group_points"][group_id]
    collector.save_groups(groups_data["common_points"], groups_data["group_points"])
    
    return jsonify({"success": True, "message": f"设备 {group_id} 已删除"})

import os

@app.route('/api/scripts/categories', methods=['GET'])
def get_script_categories():
    try:
        script_dir = '话术文件'
        if not os.path.exists(script_dir):
            return jsonify({"success": False, "message": "话术文件目录不存在"})
        
        products = []
        # 获取所有JSON文件并按名称排序
        json_files = sorted([f for f in os.listdir(script_dir) if f.endswith('.json')])
        
        for filename in json_files:
            product = filename[:-5]
            products.append(product)
        
        return jsonify({"success": True, "products": products})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/categories', methods=['GET'])
def get_categories_by_product(product):
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        categories = list(scripts.keys())
        return jsonify({"success": True, "categories": categories})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/<category>', methods=['GET'])
def get_scripts_by_product_category(product, category):
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category not in scripts:
            return jsonify({"success": False, "message": f"类目 {category} 不存在"})
        
        return jsonify({"success": True, "scripts": scripts[category]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/<category>', methods=['POST'])
def add_script(product, category):
    try:
        data = request.json
        script = data.get('script', '')
        
        if not script:
            return jsonify({"success": False, "message": "话术内容不能为空"})
        
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            scripts = {}
        else:
            with open(script_file, 'r', encoding='utf-8') as f:
                scripts = json.load(f)
        
        if category not in scripts:
            scripts[category] = []
        
        scripts[category].append(script)
        
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "话术添加成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/<category>', methods=['PUT'])
def update_script(product, category):
    try:
        data = request.json
        old_script = data.get('old_script', '')
        new_script = data.get('new_script', '')
        
        if not old_script or not new_script:
            return jsonify({"success": False, "message": "话术内容不能为空"})
        
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category not in scripts:
            return jsonify({"success": False, "message": f"类目 {category} 不存在"})
        
        if old_script not in scripts[category]:
            return jsonify({"success": False, "message": "原话术不存在"})
        
        index = scripts[category].index(old_script)
        scripts[category][index] = new_script
        
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "话术修改成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/<category>', methods=['DELETE'])
def delete_script(product, category):
    try:
        data = request.json
        script = data.get('script', '')
        
        if not script:
            return jsonify({"success": False, "message": "话术内容不能为空"})
        
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category not in scripts:
            return jsonify({"success": False, "message": f"类目 {category} 不存在"})
        
        if script not in scripts[category]:
            return jsonify({"success": False, "message": "话术不存在"})
        
        scripts[category].remove(script)
        
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "话术删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        product = data.get('product', '')
        
        if not product:
            return jsonify({"success": False, "message": "产品名称不能为空"})
        
        script_file = os.path.join('话术文件', f'{product}.json')
        if os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 已存在"})
        
        # 创建新的产品文件，初始为空对象
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": f"产品 {product} 创建成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/products/<product>', methods=['DELETE'])
def delete_product(product):
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        # 删除产品文件
        os.remove(script_file)
        
        return jsonify({"success": True, "message": f"产品 {product} 删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/categories', methods=['POST'])
def create_category(product):
    try:
        data = request.json
        category = data.get('category', '')
        
        if not category:
            return jsonify({"success": False, "message": "类目名称不能为空"})
        
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category in scripts:
            return jsonify({"success": False, "message": f"类目 {category} 已存在"})
        
        scripts[category] = []
        
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": f"类目 {category} 创建成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scripts/<product>/categories/<category>', methods=['DELETE'])
def delete_category(product, category):
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        if category not in scripts:
            return jsonify({"success": False, "message": f"类目 {category} 不存在"})
        
        del scripts[category]
        
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": f"类目 {category} 删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch-messages', methods=['GET'])
def get_batch_messages():
    try:
        with open('群发消息.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch-messages', methods=['POST'])
def add_batch_message():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({"success": False, "message": "消息内容不能为空"})
        
        with open('群发消息.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        messages.append(message)
        
        with open('群发消息.json', 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "群发消息添加成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch-messages', methods=['PUT'])
def update_batch_message():
    try:
        data = request.json
        old_message = data.get('old_message', '')
        new_message = data.get('new_message', '')
        
        if not old_message or not new_message:
            return jsonify({"success": False, "message": "消息内容不能为空"})
        
        with open('群发消息.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if old_message not in messages:
            return jsonify({"success": False, "message": "原消息不存在"})
        
        index = messages.index(old_message)
        messages[index] = new_message
        
        with open('群发消息.json', 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "群发消息修改成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch-messages', methods=['DELETE'])
def delete_batch_message():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({"success": False, "message": "消息内容不能为空"})
        
        with open('群发消息.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if message not in messages:
            return jsonify({"success": False, "message": "消息不存在"})
        
        messages.remove(message)
        
        with open('群发消息.json', 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "群发消息删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scheduled-messages', methods=['GET', 'POST'])
def scheduled_messages():
    if request.method == 'GET':
        try:
            with open('定期发送话术.json', 'r', encoding='utf-8') as f:
                messages = json.load(f)
            return jsonify({"success": True, "messages": messages})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    elif request.method == 'POST':
        try:
            data = request.json
            action = data.get('action', '')
            
            with open('定期发送话术.json', 'r', encoding='utf-8') as f:
                messages = json.load(f)
            
            if action == 'add':
                new_message = data.get('message', '').strip()
                if new_message:
                    messages.append(new_message)
                    with open('定期发送话术.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术添加成功"})
                else:
                    return jsonify({"success": False, "message": "话术内容不能为空"})
            
            elif action == 'delete':
                index = data.get('index', -1)
                if 0 <= index < len(messages):
                    messages.pop(index)
                    with open('定期发送话术.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术删除成功"})
                else:
                    return jsonify({"success": False, "message": "索引无效"})
            
            elif action == 'edit':
                index = data.get('index', -1)
                new_message = data.get('message', '').strip()
                if 0 <= index < len(messages) and new_message:
                    messages[index] = new_message
                    with open('定期发送话术.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术编辑成功"})
                else:
                    return jsonify({"success": False, "message": "索引无效或话术内容不能为空"})
            
            else:
                return jsonify({"success": False, "message": "无效的操作"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch-messages', methods=['GET', 'POST'])
def batch_messages():
    if request.method == 'GET':
        try:
            with open('群发消息.json', 'r', encoding='utf-8') as f:
                messages = json.load(f)
            return jsonify({"success": True, "messages": messages})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    elif request.method == 'POST':
        try:
            data = request.json
            action = data.get('action', '')
            
            with open('群发消息.json', 'r', encoding='utf-8') as f:
                messages = json.load(f)
            
            if action == 'add':
                new_message = data.get('message', '').strip()
                if new_message:
                    messages.append(new_message)
                    with open('群发消息.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术添加成功"})
                else:
                    return jsonify({"success": False, "message": "话术内容不能为空"})
            
            elif action == 'delete':
                index = data.get('index', -1)
                if 0 <= index < len(messages):
                    messages.pop(index)
                    with open('群发消息.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术删除成功"})
                else:
                    return jsonify({"success": False, "message": "索引无效"})
            
            elif action == 'edit':
                index = data.get('index', -1)
                new_message = data.get('message', '').strip()
                if 0 <= index < len(messages) and new_message:
                    messages[index] = new_message
                    with open('群发消息.json', 'w', encoding='utf-8') as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    return jsonify({"success": True, "message": "话术编辑成功"})
                else:
                    return jsonify({"success": False, "message": "索引无效或话术内容不能为空"})
            
            else:
                return jsonify({"success": False, "message": "无效的操作"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch/start', methods=['POST'])
def start_batch_control():
    global batch_control_thread, batch_control_running, keyboard_listener
    
    if batch_control_running:
        return jsonify({"success": False, "message": "群控正在运行中"})
    
    data = request.json
    product = data.get('product', '')
    category_probabilities = data.get('category_probabilities', {})
    speed = data.get('speed', '中')
    
    if not product:
        return jsonify({"success": False, "message": "产品不能为空"})
    
    if not category_probabilities:
        return jsonify({"success": False, "message": "分类概率设置不能为空"})
    
    total_category_probability = sum(category_probabilities.values())
    if total_category_probability <= 0:
        return jsonify({"success": False, "message": "分类总概率必须大于0"})
    
    if total_category_probability > 1:
        return jsonify({"success": False, "message": "分类总概率不能超过100%"})
    
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            return jsonify({"success": False, "message": f"产品 {product} 不存在"})
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        for category in category_probabilities.keys():
            if category not in scripts:
                return jsonify({"success": False, "message": f"产品 {product} 中的分类 {category} 不存在"})
        
        batch_control_running = True
        batch_control_thread = threading.Thread(target=batch_control_worker, args=(product, category_probabilities, speed))
        batch_control_thread.start()
        
        return jsonify({"success": True, "message": f"开始群控，按ESC键可快速停止"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/click-all', methods=['POST'])
def click_all_common_points():
    try:
        data = request.json
        group_id = data.get('group_id', '')
        message = data.get('message', '')
        speed = data.get('speed', '中')
        use_file = data.get('use_file', False)
        
        if not group_id:
            return jsonify({"success": False, "message": "设备ID不能为空"})
        
        if not use_file and not message:
            return jsonify({"success": False, "message": "消息内容不能为空"})
        
        if use_file:
            # 从文件读取话术并群发
            import json
            import os
            from random import choice
            
            scheduled_messages_file = os.path.join(app.root_path, '定期发送话术.json')
            if not os.path.exists(scheduled_messages_file):
                return jsonify({"success": False, "message": "定期发送话术.json文件不存在"})
            
            with open(scheduled_messages_file, 'r', encoding='utf-8') as f:
                scheduled_data = json.load(f)
            
            messages = scheduled_data.get('messages', [])
            if not messages:
                return jsonify({"success": False, "message": "定期发送话术.json文件中没有话术"})
            
            # 选择一个随机话术
            selected_message = choice(messages)
            send_message_all(selected_message, group_id, speed)
            return jsonify({"success": True, "message": f"群发消息完成（从文件读取）: {selected_message}"})
        else:
            send_message_all(message, group_id, speed)
            return jsonify({"success": True, "message": "群发消息完成"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/group-mode/enter', methods=['POST'])
def enter_group_mode_api():
    try:
        enter_group_mode()
        return jsonify({"success": True, "message": "进入群发模式完成"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/group-mode/exit', methods=['POST'])
def exit_group_mode_api():
    try:
        exit_group_mode()
        return jsonify({"success": True, "message": "退出群发模式完成"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch/stop', methods=['POST'])
def stop_batch_control():
    global batch_control_running
    
    if not batch_control_running:
        return jsonify({"success": False, "message": "群控未在运行"})
    
    batch_control_running = False
    
    return jsonify({"success": True, "message": "群控已停止"})

@app.route('/api/batch/update-probabilities', methods=['POST'])
def update_batch_probabilities():
    global batch_control_running, batch_control_status
    
    if not batch_control_running:
        return jsonify({"success": False, "message": "群控未在运行"})
    
    data = request.json
    category_probabilities = data.get('category_probabilities', {})
    
    if not category_probabilities:
        return jsonify({"success": False, "message": "分类概率设置不能为空"})
    
    total_category_probability = sum(category_probabilities.values())
    if total_category_probability <= 0:
        return jsonify({"success": False, "message": "分类总概率必须大于0"})
    
    if total_category_probability > 1:
        return jsonify({"success": False, "message": "分类总概率不能超过100%"})
    
    try:
        # 更新全局概率分布
        global current_category_probabilities
        current_category_probabilities = category_probabilities
        
        batch_control_status["message"] = "概率分布已更新"
        
        return jsonify({"success": True, "message": "概率分布已更新"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/batch/status', methods=['GET'])
def get_batch_status():
    return jsonify(batch_control_status)

def batch_control_worker(product, category_probabilities, speed):
    global batch_control_status, batch_control_running, global_keyboard_listener, current_category_probabilities
    
    # 初始化全局概率分布变量
    current_category_probabilities = category_probabilities
    
    if global_keyboard_listener is None:
        global_keyboard_listener = keyboard.Listener(on_press=on_global_key_press)
        global_keyboard_listener.start()
    
    try:
        script_file = os.path.join('话术文件', f'{product}.json')
        if not os.path.exists(script_file):
            batch_control_status["status"] = "error"
            batch_control_status["message"] = f"产品 {product} 不存在"
            batch_control_running = False
            return
        
        with open(script_file, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        
        # 验证初始概率分布中的分类
        for category in category_probabilities.keys():
            if category not in scripts:
                batch_control_status["status"] = "error"
                batch_control_status["message"] = f"产品 {product} 中的分类 {category} 不存在"
                batch_control_running = False
                return
        
        groups_data = collector.load_groups()
        if groups_data is None:
            batch_control_status["status"] = "error"
            batch_control_status["message"] = "无法读取设备数据文件"
            batch_control_running = False
            return
        
        group_ids = list(groups_data.get("group_points", {}).keys())
        if not group_ids:
            batch_control_status["status"] = "error"
            batch_control_status["message"] = "没有可用的设备"
            batch_control_running = False
            return
        
        batch_control_status["status"] = "running"
        batch_control_status["category"] = f"{product} - {', '.join(category_probabilities.keys())}"
        batch_control_status["sent_count"] = 0
        
        # 初始化已发送话术记录（使用索引而不是内容）
        sent_messages = {}
        for category in category_probabilities.keys():
            sent_messages[category] = []
        
        def select_category_by_probability():
            # 使用全局概率分布变量，支持动态更新
            categories = current_category_probabilities
            if not categories:
                return None
            r = random.random()
            cumulative = 0
            for category, prob in categories.items():
                cumulative += prob
                if r <= cumulative:
                    return category
            return list(categories.keys())[0]
        
        def select_message_by_category(category):
            # 验证分类是否存在
            if category not in scripts:
                return None
            
            # 初始化新分类的已发送记录
            if category not in sent_messages:
                sent_messages[category] = []
            
            messages = scripts.get(category, [])
            if not messages:
                return None
            
            # 获取未发送的索引
            total_messages = len(messages)
            unsent_indices = [i for i in range(total_messages) if i not in sent_messages[category]]
            
            # 如果所有索引都已发送，清空已发送记录
            if not unsent_indices:
                sent_messages[category].clear()
                unsent_indices = list(range(total_messages))
            
            # 随机选择一个未发送的索引
            selected_index = random.choice(unsent_indices)
            selected_message = messages[selected_index]
            # 记录到已发送列表
            sent_messages[category].append(selected_index)
            
            return selected_message
        
        while batch_control_running:
            for group_id in group_ids:
                if not batch_control_running:
                    break
                
                selected_category = select_category_by_probability()
                
                if not selected_category:
                    continue
                
                message = select_message_by_category(selected_category)
                
                if not message:
                    continue
                
                batch_control_status["current_group"] = group_id
                batch_control_status["message"] = f"正在向设备 {group_id} 发送消息（{product} - {selected_category}）：{message}"
                
                try:
                    send_message(message, group_id, speed)
                    batch_control_status["sent_count"] += 1
                except Exception as e:
                    batch_control_status["message"] = f"发送失败：{str(e)}"
                
                time.sleep(2)
        
        batch_control_status["status"] = "idle"
        batch_control_status["message"] = "群控已停止"
        batch_control_running = False
        
    except Exception as e:
        batch_control_status["status"] = "error"
        batch_control_status["message"] = f"群控出错：{str(e)}"
        batch_control_running = False

@app.route('/api/scheduled/start', methods=['POST'])
def start_scheduled_send():
    global scheduled_send_thread, scheduled_send_running, global_keyboard_listener
    
    if scheduled_send_running:
        return jsonify({"success": False, "message": "定期发送正在运行中"})
    
    data = request.json
    message = data.get('message', '')
    group_id = data.get('group_id', '')
    interval = data.get('interval', 60)
    use_file = data.get('use_file', False)
    
    if not group_id:
        return jsonify({"success": False, "message": "设备ID不能为空"})
    
    if interval < 1:
        return jsonify({"success": False, "message": "时间间隔必须至少为1秒"})
    
    if not use_file and not message:
        return jsonify({"success": False, "message": "消息内容不能为空"})
    
    try:
        groups_data = collector.load_groups()
        if groups_data is None:
            return jsonify({"success": False, "message": "无法读取设备数据文件"})
        
        if group_id != 'random' and group_id not in groups_data.get("group_points", {}):
            return jsonify({"success": False, "message": f"设备 {group_id} 不存在"})
        
        scheduled_send_running = True
        scheduled_send_thread = threading.Thread(target=scheduled_send_worker, args=(message, group_id, interval, use_file))
        scheduled_send_thread.start()
        
        if global_keyboard_listener is None:
            global_keyboard_listener = keyboard.Listener(on_press=on_global_key_press)
            global_keyboard_listener.start()
        
        if use_file:
            return jsonify({"success": True, "message": f"开始从文件读取话术定期发送，按ESC键可快速停止"})
        else:
            return jsonify({"success": True, "message": f"开始定期发送，按ESC键可快速停止"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/scheduled/stop', methods=['POST'])
def stop_scheduled_send():
    global scheduled_send_running
    
    if not scheduled_send_running:
        return jsonify({"success": False, "message": "定期发送未在运行"})
    
    scheduled_send_running = False
    
    return jsonify({"success": True, "message": "定期发送已停止"})

@app.route('/api/scheduled/status', methods=['GET'])
def get_scheduled_send_status():
    return jsonify(scheduled_send_status)

def scheduled_send_worker(message, group_id, interval, use_file):
    global scheduled_send_status, scheduled_send_running
    
    # 初始化已发送话术记录
    sent_messages = []
    scheduled_messages = []
    
    # 如果使用文件，加载话术列表
    if use_file:
        try:
            with open('定期发送话术.json', 'r', encoding='utf-8') as f:
                scheduled_messages = json.load(f)
        except Exception as e:
            scheduled_send_status["status"] = "error"
            scheduled_send_status["message"] = f"无法读取定期发送话术文件：{str(e)}"
            scheduled_send_running = False
            return
    
    try:
        scheduled_send_status["status"] = "running"
        scheduled_send_status["group_id"] = group_id
        scheduled_send_status["sent_count"] = 0
        
        if use_file:
            scheduled_send_status["message"] = f"开始从文件读取话术定期发送到设备 {group_id}，间隔 {interval} 秒"
        else:
            scheduled_send_status["message"] = f"开始定期发送消息到设备 {group_id}，间隔 {interval} 秒"
        
        groups_data = collector.load_groups()
        if groups_data is None:
            scheduled_send_status["status"] = "error"
            scheduled_send_status["message"] = "无法读取设备数据文件"
            scheduled_send_running = False
            return
        
        group_ids = list(groups_data.get("group_points", {}).keys())
        if not group_ids:
            scheduled_send_status["status"] = "error"
            scheduled_send_status["message"] = "没有可用的设备"
            scheduled_send_running = False
            return
        
        if group_id == 'random':
            if use_file:
                scheduled_send_status["message"] = f"开始随机从文件读取话术定期发送，间隔 {interval} 秒"
            else:
                scheduled_send_status["message"] = f"开始随机定期发送消息，间隔 {interval} 秒"
        
        def get_next_message():
            if not use_file:
                return message
            
            # 从文件中选择未发送的话术
            if not scheduled_messages:
                return None
            
            # 获取未发送的话术
            unsent_messages = [msg for msg in scheduled_messages if msg not in sent_messages]
            
            # 如果所有话术都已发送，清空已发送记录
            if not unsent_messages:
                sent_messages.clear()
                unsent_messages = scheduled_messages[:]
            
            # 随机选择一条未发送的话术
            selected_message = random.choice(unsent_messages)
            # 记录到已发送列表
            sent_messages.append(selected_message)
            
            return selected_message
        
        while scheduled_send_running:
            next_send_time = time.time() + interval
            scheduled_send_status["next_send_time"] = next_send_time
            
            while scheduled_send_running and time.time() < next_send_time:
                time.sleep(0.1)
            
            if not scheduled_send_running:
                break
            
            # 获取要发送的消息
            current_message = get_next_message()
            if not current_message:
                scheduled_send_status["message"] = "没有可用的话术"
                continue
            
            target_group_id = group_id
            if group_id == 'random':
                target_group_id = random.choice(group_ids)
                if use_file:
                    scheduled_send_status["message"] = f"正在向随机设备 {target_group_id} 发送话术：{current_message}"
                else:
                    scheduled_send_status["message"] = f"正在向随机设备 {target_group_id} 发送消息：{current_message}"
            else:
                if use_file:
                    scheduled_send_status["message"] = f"正在向设备 {group_id} 发送话术：{current_message}"
                else:
                    scheduled_send_status["message"] = f"正在向设备 {group_id} 发送消息：{current_message}"
            
            try:
                send_message(current_message, target_group_id)
                scheduled_send_status["sent_count"] += 1
                if group_id == 'random':
                    scheduled_send_status["message"] = f"消息已发送到随机设备 {target_group_id}，共发送 {scheduled_send_status['sent_count']} 次"
                else:
                    scheduled_send_status["message"] = f"消息已发送到设备 {group_id}，共发送 {scheduled_send_status['sent_count']} 次"
            except Exception as e:
                scheduled_send_status["message"] = f"发送失败：{str(e)}"
        
        scheduled_send_status["status"] = "idle"
        scheduled_send_status["message"] = "定期发送已停止"
        scheduled_send_status["next_send_time"] = None
        scheduled_send_running = False
        
    except Exception as e:
        scheduled_send_status["status"] = "error"
        scheduled_send_status["message"] = f"定期发送出错：{str(e)}"
        scheduled_send_running = False

if __name__ == '__main__':
    app.run(debug=True, port=5000)
