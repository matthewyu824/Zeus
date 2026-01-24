import pyautogui
from pynput import mouse
import time
import json
import os
import pyperclip

POINTS_FILE = "collected_points.json"
GROUPS_FILE = "groups.json"

class PointCollector:
    def __init__(self):
        self.points = []
        self.listener = None
        self.collecting = True
        self.common_points = []
        self.group_points = {}

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.points.append((x, y))
            print(f"已收集第 {len(self.points)} 个点: ({x}, {y})")
            
            if len(self.points) >= 5:
                self.collecting = False
                return False

    def collect_points(self):
        print("请在屏幕上点击 5 个位置来收集坐标点...")
        print("点击鼠标左键来记录位置")
        
        self.points = []
        self.collecting = True
        
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()
        
        print(f"\n收集完成！5 个点的坐标：")
        for i, point in enumerate(self.points, 1):
            print(f"点 {i}: {point}")
        
        return self.points

    def save_points_to_file(self, points):
        with open(POINTS_FILE, 'w') as f:
            json.dump(points, f)
        print(f"\n坐标点已保存到文件: {POINTS_FILE}")

    def load_points_from_file(self):
        if not os.path.exists(POINTS_FILE):
            print(f"错误：文件 {POINTS_FILE} 不存在")
            return None
        
        with open(POINTS_FILE, 'r') as f:
            points = json.load(f)
        
        return points

    def save_groups(self, common_points, group_points):
        data = {
            "common_points": common_points,
            "group_points": group_points
        }
        with open(GROUPS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n组数据已保存到文件: {GROUPS_FILE}")

    def load_groups(self):
        if not os.path.exists(GROUPS_FILE):
            return None
        
        with open(GROUPS_FILE, 'r') as f:
            data = json.load(f)
        
        return data

    def collect_common_points(self):
        print("\n请收集公共点（6个点）...")
        print("点击鼠标左键来记录位置")
        
        self.common_points = []
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                self.common_points.append((x, y))
                print(f"已收集第 {len(self.common_points)} 个公共点: ({x}, {y})")
                
                if len(self.common_points) >= 6:
                    return False
        
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        
        print(f"\n公共点收集完成！")
        for i, point in enumerate(self.common_points, 1):
            print(f"公共点 {i}: {point}")
        
        return self.common_points

    def collect_group_points(self, group_id):
        print(f"\n请收集组 {group_id} 的特定点（点1、点4、点5）...")
        print("点击鼠标左键来记录位置")
        
        group_points = []
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                group_points.append((x, y))
                print(f"已收集第 {len(group_points)} 个特定点: ({x}, {y})")
                
                if len(group_points) >= 3:
                    return False
        
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        
        print(f"\n组 {group_id} 特定点收集完成！")
        for i, point in enumerate(group_points, 1):
            print(f"特定点 {i}: {point}")
        
        return group_points

    def execute_clicks(self, points):
        if len(points) != 4:
            print("错误：需要 4 个点才能执行点击操作")
            return
        
        print("\n开始依次点击 4 个位置...")
        
        for i, (x, y) in enumerate(points, 1):
            print(f"点击第 {i} 个位置: ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(1)
            
            if i == 2:
                print("输入文字：厉害")
                pyperclip.copy('好听')
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1)
        
        print("\n点击操作完成！")

def collect_points_to_file():
    collector = PointCollector()
    
    points = collector.collect_points()
    
    if len(points) == 5:
        collector.save_points_to_file(points)
    else:
        print("收集的点数量不足")

def execute_clicks_from_file():
    collector = PointCollector()
    
    points = collector.load_points_from_file()
    
    if points is None:
        return
    
    print(f"\n从文件读取到 {len(points)} 个坐标点：")
    for i, point in enumerate(points, 1):
        print(f"点 {i}: {point}")
    
    print("\n准备执行点击操作...")
    time.sleep(2)
    
    collector.execute_clicks(points)

def send_message(message, group_id, speed='中'):
    collector = PointCollector()
    
    groups_data = collector.load_groups()
    
    if groups_data is None:
        print("错误：无法读取组数据文件")
        return
    
    common_points = groups_data.get("common_points", [])
    group_points = groups_data.get("group_points", {})
    
    if group_id not in group_points:
        print(f"错误：组 {group_id} 不存在")
        return
    
    if len(common_points) < 2:
        print("错误：公共点数据不足")
        return
    
    if len(group_points[group_id]) < 3:
        print(f"错误：组 {group_id} 的特定点数据不足")
        return
    
    group_specific = group_points[group_id]
    
    speed_map = {'快': 0.3, '中': 0.5, '慢': 0.7}
    sleep_time = speed_map.get(speed, 0.5)
    
    print(f"\n发送消息: {message}")
    print(f"使用组 {group_id} 的标注点")
    print(f"速度设置: {speed} (sleep_time={sleep_time})")
    
    x, y = group_specific[0]
    print(f"点击第1个位置（组{group_id} 点1）: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(sleep_time)

    print(f"输入文字: {message}")
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(sleep_time)
    
    x, y = group_specific[1]

    print(f"点击第2个位置（组{group_id} 点2）: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(sleep_time)

    x, y = group_specific[2]

    print(f"点击第2个位置（组{group_id} 点2）: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(0.1)
    
    print("\n消息发送完成！")

def send_message_all(message, group_id, speed='中'):
    collector = PointCollector()
    
    groups_data = collector.load_groups()
    
    if groups_data is None:
        print("错误：无法读取组数据文件")
        return
    
    group_points = groups_data.get("group_points", {})
    
    if group_id not in group_points:
        print(f"错误：设备 {group_id} 不存在")
        return
    
    points = group_points[group_id]
    
    if len(points) < 3:
        print(f"错误：设备 {group_id} 需要至少3个点")
        return
    
    speed_map = {'快': 0.3, '中': 0.5, '慢': 0.7}
    sleep_time = speed_map.get(speed, 0.5)
    
    print(f"\n开始群发消息...")
    print(f"设备ID：{group_id}")
    print(f"消息内容：{message}")
    print(f"速度设置: {speed} (sleep_time={sleep_time})")
    
    x, y = points[0]
    print(f"第一步：左键点击第1个点: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(sleep_time)
    
    print(f"第二步：复制消息并粘贴到输入框")
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(sleep_time)
    
    x, y = points[1]
    print(f"第三步：点击第2个点: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(sleep_time)
    
    x, y = points[2]
    print(f"第四步：点击第3个点: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(sleep_time)
    
    print("\n群发消息完成！")

def enter_group_mode():
    collector = PointCollector()
    
    groups_data = collector.load_groups()
    
    if groups_data is None:
        print("错误：无法读取组数据文件")
        return
    
    common_points = groups_data.get("common_points", [])
    
    if len(common_points) < 3:
        print("错误：公共点数据不足，需要至少3个公共点")
        return
    
    print(f"\n进入群发模式...")
    print(f"使用公共点进行操作")
    
    x, y = common_points[0]
    print(f"第一步：左键点击公共点1: ({x}, {y})")
    pyautogui.click(x, y, button='right')
    time.sleep(0.5)
    
    x, y = common_points[1]
    print(f"第二步：左键点击公共点2: ({x}, {y})")
    pyautogui.click(x, y, button='right')
    time.sleep(0.5)
    
    x, y = common_points[2]
    print(f"第三步：右键点击公共点3: ({x}, {y})")
    pyautogui.click(x, y, button='right')
    time.sleep(0.5)
    
    x, y = common_points[2]
    print(f"第四步：左键点击公共点3: ({x}, {y})")
    pyautogui.click(x, y, button='left')
    time.sleep(0.5)
    
    print("\n进入群发模式完成！")

def exit_group_mode():
    collector = PointCollector()
    
    groups_data = collector.load_groups()
    
    if groups_data is None:
        print("错误：无法读取组数据文件")
        return
    
    common_points = groups_data.get("common_points", [])
    
    if len(common_points) < 4:
        print("错误：公共点数据不足，需要至少4个公共点")
        return
    
    print(f"\n退出群发模式...")
    print(f"使用公共点进行操作")
    
    x, y = common_points[0]
    print(f"第一步：左键点击公共点1: ({x}, {y})")
    pyautogui.click(x, y, button='left')
    time.sleep(0.5)
    
    x, y = common_points[1]
    print(f"第二步：左键点击公共点2: ({x}, {y})")
    pyautogui.click(x, y, button='left')
    time.sleep(0.5)
    
    x, y = common_points[2]
    print(f"第三步：右键点击公共点3: ({x}, {y})")
    pyautogui.click(x, y, button='right')
    time.sleep(0.5)
    
    x, y = common_points[3]
    print(f"第四步：左键点击公共点4: ({x}, {y})")
    pyautogui.click(x, y, button='left')
    time.sleep(0.5)
    
    print("\n退出群发模式完成！")

def main():
    print("请选择操作：")
    print("1. 收集公共点（6个点）")
    print("2. 收集组特定点（点1、点4、点5）")
    print("3. 发送消息（使用 send_message 函数）")
    print("4. 点击所有公共点（使用 send_message_all 函数）")
    print("5. 查看所有组信息")
    
    choice = input("\n请输入选项 (1, 2, 3, 4 或 5): ").strip()
    
    collector = PointCollector()
    groups_data = collector.load_groups()
    
    if groups_data is None:
        groups_data = {"common_points": [], "group_points": {}}
    
    if choice == "1":
        common_points = collector.collect_common_points()
        groups_data["common_points"] = common_points
        collector.save_groups(groups_data["common_points"], groups_data["group_points"])
        
    elif choice == "2":
        group_id = input("请输入组ID（如 group1, group2 等）: ").strip()
        group_points = collector.collect_group_points(group_id)
        groups_data["group_points"][group_id] = group_points
        collector.save_groups(groups_data["common_points"], groups_data["group_points"])
        
    elif choice == "3":
        message = input("请输入要发送的消息: ").strip()
        group_id = input("请输入组ID: ").strip()
        print("\n请选择速度：")
        print("1. 快 (0.3秒)")
        print("2. 中 (0.5秒)")
        print("3. 慢 (0.7秒)")
        speed_choice = input("请输入速度选项 (1, 2 或 3，默认为2): ").strip()
        speed_map = {'1': '快', '2': '中', '3': '慢'}
        speed = speed_map.get(speed_choice, '中')
        send_message(message, group_id, speed)
        
    elif choice == "4":
        message = input("请输入要发送的消息: ").strip()
        print("\n请选择速度：")
        print("1. 快 (0.3秒)")
        print("2. 中 (0.5秒)")
        print("3. 慢 (0.7秒)")
        speed_choice = input("请输入速度选项 (1, 2 或 3，默认为2): ").strip()
        speed_map = {'1': '快', '2': '中', '3': '慢'}
        speed = speed_map.get(speed_choice, '中')
        send_message_all(message, speed)
        
    elif choice == "5":
        print("\n=== 组信息 ===")
        print(f"公共点数量: {len(groups_data['common_points'])}")
        for i, point in enumerate(groups_data['common_points'], 1):
            print(f"  公共点 {i}: {point}")
        
        print(f"\n组数量: {len(groups_data['group_points'])}")
        for group_id, points in groups_data['group_points'].items():
            print(f"\n组 {group_id}:")
            for i, point in enumerate(points, 1):
                print(f"  特定点 {i}: {point}")
    else:
        print("无效的选项")

if __name__ == "__main__":
    main()
