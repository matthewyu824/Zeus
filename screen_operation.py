import pyautogui
from pynput import mouse
import time
import json
import os
import pyperclip

POINTS_FILE = "collected_points.json"

class PointCollector:
    def __init__(self):
        self.points = []
        self.listener = None
        self.collecting = True

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.points.append((x, y))
            print(f"已收集第 {len(self.points)} 个点: ({x}, {y})")
            
            if len(self.points) >= 4:
                self.collecting = False
                return False

    def collect_points(self):
        print("请在屏幕上点击 4 个位置来收集坐标点...")
        print("点击鼠标左键来记录位置")
        
        self.points = []
        self.collecting = True
        
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()
        
        print(f"\n收集完成！4 个点的坐标：")
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

    def execute_clicks(self, points):
        if len(points) != 4:
            print("错误：需要 4 个点才能执行点击操作")
            return
        
        print("\n开始依次点击 4 个位置...")
        
        for i, (x, y) in enumerate(points, 1):
            print(f"点击第 {i} 个位置: ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(1)
            
            if i == 1:
                print("输入文字：厉害")
                pyperclip.copy('好听')
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1)
        
        print("\n点击操作完成！")

def collect_points_to_file():
    collector = PointCollector()
    
    points = collector.collect_points()
    
    if len(points) == 4:
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

def send_message(message):
    collector = PointCollector()
    
    points = collector.load_points_from_file()
    
    if points is None:
        print("错误：无法读取坐标点文件")
        return
    
    if len(points) < 2:
        print("错误：需要至少 2 个坐标点")
        return
    
    print(f"\n发送消息: {message}")
    print(f"使用 {len(points)} 个坐标点")
    
    x, y = points[0]
    print(f"点击第 1 个位置: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(1)
    
    print(f"输入文字: {message}")
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    
    for i, (x, y) in enumerate(points[1:], 2):
        print(f"点击第 {i} 个位置: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(1)
    
    print("\n消息发送完成！")

def main():
    print("请选择操作：")
    print("1. 收集坐标点并保存到文件")
    print("2. 从文件读取坐标点并执行点击")
    print("3. 发送消息（使用 send_message 函数）")
    
    choice = input("\n请输入选项 (1, 2 或 3): ").strip()
    
    if choice == "1":
        collect_points_to_file()
    elif choice == "2":
        execute_clicks_from_file()
    elif choice == "3":
        # message = input("请输入要发送的消息: ").strip()
        send_message("好听")
    else:
        print("无效的选项")

if __name__ == "__main__":
    main()
