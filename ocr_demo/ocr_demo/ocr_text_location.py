import cv2
import pytesseract
from PIL import Image
import numpy as np

class TextLocator:
    def __init__(self, tesseract_path=None):
        """
        初始化文本定位器
        :param tesseract_path: Tesseract OCR的安装路径，如Windows下需要指定
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
    def find_text_position(self, image_path, target_text, lang='chi_sim', confidence_threshold=0.5):
        """
        在图片中查找指定文本的位置
        :param image_path: 图片路径
        :param target_text: 要查找的目标文本
        :param lang: OCR语言，默认中文简体
        :param confidence_threshold: 置信度阈值，默认为0.5
        :return: 包含目标文本位置的列表，每个元素为(x, y, w, h, text, confidence)
        """
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片: {image_path}")
        
        # 转换为RGB格式
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 使用Tesseract进行OCR，获取详细数据
        custom_config = f'--oem 3 --psm 6 -l {lang}'
        data = pytesseract.image_to_data(rgb_img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # 存储结果
        results = []
        
        # 遍历所有检测到的文本块
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            # 获取置信度
            conf = int(data['conf'][i])
            if conf < confidence_threshold * 100:
                continue
            
            # 获取文本
            text = data['text'][i].strip()
            if not text:
                continue
            
            # 检查是否包含目标文本
            if target_text in text:
                # 获取位置信息
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # 添加到结果列表
                results.append((x, y, w, h, text, conf / 100.0))
        
        return results
    
    def draw_text_boxes(self, image_path, target_text, output_path, lang='chi_sim', confidence_threshold=0.5):
        """
        在图片上绘制检测到的文本框并保存
        :param image_path: 输入图片路径
        :param target_text: 要查找的目标文本
        :param output_path: 输出图片路径
        :param lang: OCR语言
        :param confidence_threshold: 置信度阈值
        :return: 检测到的文本位置列表
        """
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片: {image_path}")
        
        # 查找文本位置
        positions = self.find_text_position(image_path, target_text, lang, confidence_threshold)
        
        # 绘制文本框
        for (x, y, w, h, text, conf) in positions:
            # 绘制矩形框
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # 绘制文本
            cv2.putText(img, f"{text} ({conf:.2f})", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 保存图片
        cv2.imwrite(output_path, img)
        print(f"已保存带文本框的图片到: {output_path}")
        
        return positions

if __name__ == "__main__":
    # 示例用法
    import argparse
    
    parser = argparse.ArgumentParser(description='识别图片中指定中文字符串的位置')
    parser.add_argument('--image', type=str, required=True, help='输入图片路径')
    parser.add_argument('--target', type=str, required=True, help='要查找的目标文本')
    parser.add_argument('--output', type=str, default='output.jpg', help='输出图片路径')
    parser.add_argument('--lang', type=str, default='chi_sim', help='OCR语言，默认chi_sim（中文简体）')
    parser.add_argument('--confidence', type=float, default=0.5, help='置信度阈值，0-1之间')
    parser.add_argument('--tesseract-path', type=str, default=None, help='Tesseract OCR的安装路径')
    
    args = parser.parse_args()
    
    # 创建文本定位器
    locator = TextLocator(args.tesseract_path)
    
    # 查找并绘制文本位置
    positions = locator.draw_text_boxes(
        args.image, 
        args.target, 
        args.output, 
        args.lang, 
        args.confidence
    )
    
    # 输出结果
    if positions:
        print(f"找到{len(positions)}个匹配结果:")
        for i, (x, y, w, h, text, conf) in enumerate(positions):
            print(f"结果{i+1}: 文本='{text}'，位置=({x}, {y}, {w}, {h})，置信度={conf:.2f}")
    else:
        print("未找到匹配的文本")
