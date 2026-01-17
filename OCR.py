import os
from PIL import Image, ImageDraw

def recognize_with_easyocr(image_path, target_text='快捷话术'):
    """使用EasyOCR识别图片中的目标文字"""
    print("=" * 60)
    print("EasyOCR 识别工具")
    print("=" * 60)
    
    # 设置环境变量，跳过模型源检查
    os.environ['EASYOCR_DISABLE_MODEL_DOWNLOAD'] = '1'
    
    # 尝试导入EasyOCR
    try:
        import easyocr
        print("✓ EasyOCR 导入成功")
    except ImportError:
        print("✗ EasyOCR 未安装")
        print("请运行: pip install easyocr")
        return None
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"\n⚠ 图片不存在: {image_path}")
        print("请确保截图文件存在")
        return None
    
    print(f"\n正在识别图片: {image_path}")
    print(f"目标文字: {target_text}")
    print("-" * 60)
    
    # 创建EasyOCR reader
    try:
        print("正在初始化EasyOCR...")
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, download_enabled=False)
        print("✓ EasyOCR 初始化成功")
    except Exception as e:
        print(f"✗ EasyOCR 初始化失败: {e}")
        print("\n尝试使用离线模式...")
        try:
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            print("✓ EasyOCR 离线模式初始化成功")
        except Exception as e2:
            print(f"✗ EasyOCR 离线模式也失败: {e2}")
            return None
    
    try:
        # 使用EasyOCR进行识别
        result = reader.readtext(image_path)
        
        # 打印所有识别到的文字
        print("\n识别到的所有文字:")
        for bbox, text, confidence in result:
            print(f"  - '{text}' (置信度: {confidence:.2f})")
        
        # 查找目标文字
        for bbox, text, confidence in result:
            if target_text in text:
                # 获取边界框坐标
                left = int(bbox[0][0])
                top = int(bbox[0][1])
                right = int(bbox[2][0])
                bottom = int(bbox[2][1])
                
                width = right - left
                height = bottom - top
                
                # 计算中心点
                center_x = left + width // 2
                center_y = top + height // 2
                
                print(f"\n✓ 找到目标文字!")
                print(f"识别文字: '{text}'")
                print(f"置信度: {confidence:.2f}")
                print(f"边界框: 左上({left}, {top}), 右下({right}, {bottom})")
                print(f"尺寸: 宽{width} x 高{height}")
                print(f"中心点: ({center_x}, {center_y})")
                
                # 在图片上标注识别到的位置
                try:
                    image = Image.open(image_path)
                    draw = ImageDraw.Draw(image)
                    
                    # 绘制矩形框
                    draw.rectangle([left, top, right, bottom], outline='red', width=3)
                    
                    # 绘制中心点
                    draw.ellipse([center_x-5, center_y-5, center_x+5, center_y+5], fill='red')
                    
                    # 保存标注后的图片
                    marked_path = "marked_" + os.path.basename(image_path)
                    image.save(marked_path)
                    print(f"\n已保存标注后的图片：{marked_path}")
                except Exception as e:
                    print(f"标注图片失败: {e}")
                
                return {
                    'text': text,
                    'confidence': confidence,
                    'left': left,
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'width': width,
                    'height': height,
                    'center_x': center_x,
                    'center_y': center_y
                }
        
        print(f"\n✗ 未找到目标文字: '{target_text}'")
        return None
        
    except Exception as e:
        print(f"✗ 识别失败: {e}")
        return None

def recognize_with_tesseract(image_path, target_text='快捷话术'):
    """使用Tesseract OCR识别图片中的目标文字（备用方案）"""
    print("\n" + "=" * 60)
    print("Tesseract OCR 识别工具（备用方案）")
    print("=" * 60)
    
    # 尝试导入pytesseract
    try:
        import pytesseract
        print("✓ pytesseract 导入成功")
    except ImportError:
        print("✗ pytesseract 未安装")
        print("请运行: pip install pytesseract")
        return None
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"\n⚠ 图片不存在: {image_path}")
        print("请确保截图文件存在")
        return None
    
    print(f"\n正在识别图片: {image_path}")
    print(f"目标文字: {target_text}")
    print("-" * 60)
    
    try:
        # 图片预处理
        image = Image.open(image_path)
        image = image.convert('L')
        
        # 使用pytesseract进行识别
        data = pytesseract.image_to_data(image, lang='chi_sim', output_type=pytesseract.Output.DICT)
        
        # 打印所有识别到的文字
        print("\n识别到的所有文字:")
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                print(f"  - '{text}'")
        
        # 查找目标文字
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text and target_text in text:
                left = data['left'][i]
                top = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                
                # 计算中心点
                center_x = left + width // 2
                center_y = top + height // 2
                
                print(f"\n✓ 找到目标文字!")
                print(f"识别文字: '{text}'")
                print(f"边界框: 左上({left}, {top}), 尺寸({width}, {height})")
                print(f"中心点: ({center_x}, {center_y})")
                
                # 在图片上标注识别到的位置
                try:
                    image = Image.open(image_path)
                    draw = ImageDraw.Draw(image)
                    
                    # 绘制矩形框
                    draw.rectangle([left, top, left+width, top+height], outline='blue', width=3)
                    
                    # 绘制中心点
                    draw.ellipse([center_x-5, center_y-5, center_x+5, center_y+5], fill='blue')
                    
                    # 保存标注后的图片
                    marked_path = "marked_tesseract_" + os.path.basename(image_path)
                    image.save(marked_path)
                    print(f"\n已保存标注后的图片：{marked_path}")
                except Exception as e:
                    print(f"标注图片失败: {e}")
                
                return {
                    'text': text,
                    'left': left,
                    'top': top,
                    'width': width,
                    'height': height,
                    'center_x': center_x,
                    'center_y': center_y
                }
        
        print(f"\n✗ 未找到目标文字: '{target_text}'")
        return None
        
    except Exception as e:
        print(f"✗ 识别失败: {e}")
        print("请确保已安装Tesseract OCR并配置了中文语言包")
        return None

def main():
    """主函数"""
    # 设置图片路径
    image_path = "test.png"
    
    # 方法1: 尝试使用EasyOCR
    result = recognize_with_easyocr(image_path, '快捷话术')
    
    # 方法2: 如果EasyOCR失败，尝试Tesseract
    if not result:
        print("\n" + "=" * 60)
        print("EasyOCR失败，尝试使用Tesseract OCR...")
        result = recognize_with_tesseract(image_path, '快捷话术')
    
    # 显示最终结果
    if result:
        print("\n" + "=" * 60)
        print("识别成功!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("所有识别方法都失败")
        print("请检查:")
        print("1. 图片质量是否清晰")
        print("2. 目标文字是否正确")
        print("3. 网络连接是否正常（用于下载模型）")
        print("=" * 60)

if __name__ == "__main__":
    main()