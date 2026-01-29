import pyautogui
from PIL import Image
import time
import os
import argparse
import sys

# 配置：可以手动设置按钮位置（如果OCR无法识别）
MANUAL_BUTTON_POSITION = None  # 格式: (x, y) 或 None 使用OCR自动识别
MANUAL_INPUT_BOX_POSITION = None  # 格式: (x, y) 或 None 使用OCR自动识别

# 尝试导入PaddleOCR，如未安装则给出提示
try:
    from paddleocr import PaddleOCR
    # 使用最新的PaddleOCR API
    ocr = PaddleOCR(lang='ch')
    print("✓ PaddleOCR 加载成功")
except ImportError:
    print("⚠ PaddleOCR 未安装，请先安装PaddleOCR和PaddlePaddle:")
    print("pip install paddlepaddle")
    print("pip install paddleocr")
    sys.exit(1)
except Exception as e:
    print(f"⚠ PaddleOCR 加载失败: {e}")
    sys.exit(1)

def capture_screen(save_path='screenshot.png'):
    """捕获主屏幕并保存截图"""
    print("正在捕获主屏幕...")
    try:
        # 直接捕获主屏幕
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        print(f"屏幕截图已保存到: {save_path}")
        return save_path
    except Exception as e:
        print(f"截图失败: {e}")
        return None

def ocr_image(image_path, target_text):
    """使用PaddleOCR对图片进行OCR识别，返回目标文字的位置坐标"""
    print(f"正在使用PaddleOCR识别图片中的文字: {target_text}")
    
    try:
        # 使用最新的PaddleOCR API: predict() 替代 ocr()
        # 移除了不支持的 cls 参数
        result = ocr.predict(image_path)
        
        # 打印所有识别到的文字，用于调试
        print("识别到的所有文字:")
        all_text = []
        
        for line in result:
            for word_info in line:
                text = word_info[1][0]
                confidence = word_info[1][1]
                # 计算边界框和中心点
                points = word_info[0]
                # 四个角的坐标：左上、右上、右下、左下
                left_top = points[0]
                right_top = points[1]
                right_bottom = points[2]
                left_bottom = points[3]
                
                # 计算边界框
                left = int(min(left_top[0], right_top[0], right_bottom[0], left_bottom[0]))
                top = int(min(left_top[1], right_top[1], right_bottom[1], left_bottom[1]))
                right = int(max(left_top[0], right_top[0], right_bottom[0], left_bottom[0]))
                bottom = int(max(left_top[1], right_top[1], right_bottom[1], left_bottom[1]))
                
                width = right - left
                height = bottom - top
                
                # 计算中心点
                center_x = left + width // 2
                center_y = top + height // 2
                
                all_text.append({
                    'text': text,
                    'confidence': confidence,
                    'left': left,
                    'top': top,
                    'width': width,
                    'height': height,
                    'center_x': center_x,
                    'center_y': center_y,
                    'rect': (left, top, right, bottom)
                })
                
                print(f"   文字: '{text}', 置信度: {confidence:.2f}, 坐标: ({center_x}, {center_y}), 边界框: ({left}, {top}, {width}, {height})")
        
        # 查找包含目标文字的位置
        target_boxes = []
        for text_info in all_text:
            if target_text in text_info['text']:
                target_boxes.append(text_info)
        
        return target_boxes
        
    except Exception as e:
        print(f"OCR识别失败: {e}")
        print("尝试使用兼容模式...")
        try:
            # 兼容旧版本API
            result = ocr.ocr(image_path)
            # 处理结果的代码与上面相同
            print("识别到的所有文字:")
            all_text = []
            
            for line in result:
                for word_info in line:
                    text = word_info[1][0]
                    confidence = word_info[1][1]
                    points = word_info[0]
                    left_top = points[0]
                    right_top = points[1]
                    right_bottom = points[2]
                    left_bottom = points[3]
                    
                    left = int(min(left_top[0], right_top[0], right_bottom[0], left_bottom[0]))
                    top = int(min(left_top[1], right_top[1], right_bottom[1], left_bottom[1]))
                    right = int(max(left_top[0], right_top[0], right_bottom[0], left_bottom[0]))
                    bottom = int(max(left_top[1], right_top[1], right_bottom[1], left_bottom[1]))
                    
                    width = right - left
                    height = bottom - top
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    all_text.append({
                        'text': text,
                        'confidence': confidence,
                        'left': left,
                        'top': top,
                        'width': width,
                        'height': height,
                        'center_x': center_x,
                        'center_y': center_y,
                        'rect': (left, top, right, bottom)
                    })
                    
                    print(f"   文字: '{text}', 置信度: {confidence:.2f}, 坐标: ({center_x}, {center_y}), 边界框: ({left}, {top}, {width}, {height})")
            
            target_boxes = []
            for text_info in all_text:
                if target_text in text_info['text']:
                    target_boxes.append(text_info)
            
            return target_boxes
        except Exception as e2:
            print(f"兼容模式也失败: {e2}")
            return []

def click_at_position(x, y):
    """在指定位置执行鼠标点击"""
    print(f"正在点击位置: ({x}, {y})")
    # 保存当前鼠标位置
    current_x, current_y = pyautogui.position()
    pyautogui.click(x, y)
    # 恢复鼠标位置
    pyautogui.moveTo(current_x, current_y)
    print("点击完成")
    # 添加短暂延迟，确保操作完成
    time.sleep(1)

def type_text(text):
    """在当前焦点位置输入文字"""
    print(f"正在输入文字: {text}")
    pyautogui.typewrite(text)
    print("文字输入完成")
    time.sleep(0.5)

def main():
    # 添加命令行参数支持
    parser = argparse.ArgumentParser(description='屏幕操作工具')
    parser.add_argument('-d', '--debug', action='store_true', help='调试模式，仅测试OCR识别功能')
    args = parser.parse_args()
    
    # 捕获主屏幕
    screenshot_path = capture_screen('screenshot.png')
    
    if not screenshot_path:
        print("错误: 无法获取屏幕截图")
        sys.exit(1)
    
    # 调试模式：仅测试OCR识别功能
    if args.debug:
        print("\n=== 调试模式: 仅测试OCR识别 ===")
        
        # 测试识别"快捷话术"按钮
        print("\n1. 测试识别'快捷话术'按钮:")
        quick_reply_button_boxes = ocr_image(screenshot_path, "快捷话术")
        if quick_reply_button_boxes:
            print("✓ 成功识别到'快捷话术'按钮!")
            for i, box in enumerate(quick_reply_button_boxes):
                print(f"   位置 {i+1}: 文本='{box['text']}', 坐标=({box['center_x']}, {box['center_y']}), 边界框=({box['left']}, {box['top']}, {box['width']}, {box['height']})")
        else:
            print("✗ 未找到'快捷话术'按钮")
            
        print("\n=== 调试完成 ===")
        return
    
    # 正常模式：执行完整操作流程
    # 步骤1: 识别并点击"快捷话术按钮"
    print("\n=== 步骤1: 识别并点击'快捷话术按钮' ===")
    
    # 检查是否有手动设置的按钮位置
    if MANUAL_BUTTON_POSITION:
        print("使用手动设置的按钮位置")
        click_at_position(MANUAL_BUTTON_POSITION[0], MANUAL_BUTTON_POSITION[1])
    else:
        # 使用OCR识别按钮位置
        quick_reply_button_boxes = ocr_image(screenshot_path, "快捷话术")
        if not quick_reply_button_boxes:
            print("未找到'快捷话术按钮'")
            print("提示: 您可以在代码中设置 MANUAL_BUTTON_POSITION = (x, y) 手动指定按钮位置")
            return
        
        first_button_box = quick_reply_button_boxes[0]
        click_at_position(first_button_box['center_x'], first_button_box['center_y'])
    
    # 步骤2: 识别并点击"输入快捷回复"对话框
    print("\n=== 步骤2: 识别并点击'输入快捷回复'对话框 ===")
    
    # 检查是否有手动设置的输入框位置
    if MANUAL_INPUT_BOX_POSITION:
        print("使用手动设置的输入框位置")
        click_at_position(MANUAL_INPUT_BOX_POSITION[0], MANUAL_INPUT_BOX_POSITION[1])
    else:
        # 再次截图，因为界面可能已经变化
        screenshot_path = capture_screen('screenshot_after_button.png')
        
        # 尝试识别不同的可能文本
        input_box_boxes = ocr_image(screenshot_path, "输入快捷回复")
        if not input_box_boxes:
            print("尝试识别'输入'...")
            input_box_boxes = ocr_image(screenshot_path, "输入")
        
        if not input_box_boxes:
            print("尝试识别'快捷回复'...")
            input_box_boxes = ocr_image(screenshot_path, "快捷回复")
        
        if not input_box_boxes:
            print("未找到'输入快捷回复'对话框")
            print("提示: 您可以在代码中设置 MANUAL_INPUT_BOX_POSITION = (x, y) 手动指定输入框位置")
            return
        
        first_input_box = input_box_boxes[0]
        click_at_position(first_input_box['center_x'], first_input_box['center_y'])
    
    # 步骤3: 在当前对话框输入文字"可以可以"
    print("\n=== 步骤3: 在对话框中输入文字'可以可以' ===")
    type_text("可以可以")
    
    print("\n=== 所有操作完成 ===")

if __name__ == "__main__":
    main()