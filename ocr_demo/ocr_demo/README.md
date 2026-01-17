# 图片中文本位置识别工具

一个基于Tesseract OCR的Python工具，用于识别图片中指定中文字符串的位置。

## 功能特点

- 识别图片中指定中文文本的位置
- 返回精确的坐标信息（x, y, 宽度, 高度）
- 支持置信度过滤
- 可在图片上绘制检测结果并保存
- 命令行和API两种使用方式

## 安装说明

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装Tesseract OCR

#### macOS

```bash
brew install tesseract
brew install tesseract-lang
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-chi-sim  # 安装中文简体语言包
```

#### Windows

1. 下载Tesseract OCR安装包：[GitHub Releases](https://github.com/tesseract-ocr/tesseract/releases)
2. 安装时选择添加中文语言包
3. 记住安装路径，如：`C:\Program Files\Tesseract-OCR\tesseract.exe`

## 使用方法

### 命令行方式

```bash
python ocr_text_location.py --image <图片路径> --target <目标文本> [选项]
```

#### 选项说明

- `--image`, `-i`: 输入图片路径（必填）
- `--target`, `-t`: 要查找的目标文本（必填）
- `--output`, `-o`: 输出图片路径，默认：`output.jpg`
- `--lang`, `-l`: OCR语言，默认：`chi_sim`（中文简体）
- `--confidence`, `-c`: 置信度阈值（0-1之间），默认：`0.5`
- `--tesseract-path`, `-p`: Tesseract OCR的安装路径（Windows下需要指定）

#### 示例

```bash
# 基本使用
python ocr_text_location.py --image test.jpg --target "测试"

# 指定输出路径和置信度
python ocr_text_location.py --image test.jpg --target "测试" --output result.jpg --confidence 0.8

# Windows下指定Tesseract路径
python ocr_text_location.py --image test.jpg --target "测试" --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### API方式

```python
from ocr_text_location import TextLocator

# 初始化定位器
locator = TextLocator()

# 查找文本位置
positions = locator.find_text_position(
    image_path="test.jpg",
    target_text="测试",
    lang="chi_sim",
    confidence_threshold=0.5
)

# 绘制并保存结果
locator.draw_text_boxes(
    image_path="test.jpg",
    target_text="测试",
    output_path="output.jpg",
    lang="chi_sim",
    confidence_threshold=0.5
)
```

## 输出格式

函数返回一个列表，每个元素是一个元组，包含以下信息：

```
(x, y, width, height, text, confidence)
```

- `x, y`: 文本框左上角坐标
- `width, height`: 文本框的宽度和高度
- `text`: 检测到的文本
- `confidence`: 检测置信度（0-1之间）

## 示例输出

```
已保存带文本框的图片到: output.jpg
找到2个匹配结果:
结果1: 文本='测试文本'，位置=(100, 200, 150, 30)，置信度=0.92
结果2: 文本='测试'，位置=(300, 400, 80, 25)，置信度=0.85
```

## 技术说明

- 使用Tesseract OCR进行文本检测和识别
- 支持多种语言，默认中文简体
- 使用OpenCV进行图像处理和结果绘制
- 支持置信度过滤，提高识别准确性

## 注意事项

1. 确保Tesseract OCR已正确安装并配置
2. 对于Windows用户，必须通过`--tesseract-path`参数指定Tesseract的安装路径
3. 较高的置信度阈值可以提高准确性，但可能会漏检
4. 建议使用清晰、高对比度的图片以获得更好的识别效果
5. 对于复杂背景的图片，可能需要预处理以提高识别率

## 依赖库

- pytesseract: 用于调用Tesseract OCR
- opencv-python: 用于图像处理
- pillow: 用于图像格式转换
- numpy: 用于数值计算

## 许可证

MIT
