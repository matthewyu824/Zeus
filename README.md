# 屏幕操作工具

这是一个基于Python的屏幕操作工具，可以通过OCR识别屏幕上的文字，并在指定位置执行鼠标点击操作。

## 功能特性

1. **屏幕截图**：捕获当前屏幕并保存为图片
2. **OCR文字识别**：使用Tesseract OCR识别图片中的文字
3. **文字定位**：找到目标文字在屏幕上的位置坐标
4. **鼠标点击**：在识别到的文字位置执行鼠标点击操作

## 依赖安装

### 1. 安装Python库

```bash
pip install -r requirements.txt
```

### 2. 安装Tesseract OCR

- **Windows**：从 [GitHub](https://github.com/tesseract-ocr/tesseract/releases) 下载安装程序，安装后将 `tesseract.exe` 的路径添加到环境变量中，或在代码中修改 `pytesseract.pytesseract.tesseract_cmd` 的值
- **macOS**：使用Homebrew安装 `brew install tesseract`
- **Linux**：使用包管理器安装，如 `sudo apt install tesseract-ocr`

## 使用方法

### 基本使用

```bash
python screen_operation.py
```

默认会截图并查找文字 "测试"，然后点击第一个找到的位置。

### 命令行参数

```bash
python screen_operation.py -t <目标文字> -s <截图保存路径>
```

- `-t, --target`：要识别的目标文字（默认：测试）
- `-s, --save`：截图保存路径（默认：screenshot.png）

### 示例

```bash
python screen_operation.py -t "确认" -s "screenshot_confirm.png"
```

## 代码结构

- `capture_screen()`：捕获屏幕并保存截图
- `ocr_image()`：对图片进行OCR识别，返回目标文字的位置坐标
- `click_at_position()`：在指定位置执行鼠标点击
- `main()`：主函数，处理命令行参数并调用其他函数

## 注意事项

1. 确保Tesseract OCR已正确安装并配置路径
2. 程序需要管理员权限才能执行鼠标点击操作
3. OCR识别准确率受文字清晰度、字体大小等因素影响
4. 建议在光线充足、文字清晰的环境下使用
5. 首次运行可能需要等待依赖库加载

## 后续改进方向

1. 添加更多鼠标操作（右键点击、双击、拖拽等）
2. 支持区域截图识别
3. 添加图像识别功能，支持识别特定图像
4. 优化OCR识别准确率
5. 添加多语言支持
6. 支持群控软件上的手机屏幕操作

## 许可证

MIT License