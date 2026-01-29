import pyautogui
import time

screen_width, screen_height = pyautogui.size()
print(f"屏幕尺寸: {screen_width} x {screen_height}")
print(f"左上角: (0, 0)")
print(f"右上角: ({screen_width}, 0)")
print(f"左下角: (0, {screen_height})")
print(f"右下角: ({screen_width}, {screen_height})")
print()

time.sleep(2)

x, y = pyautogui.position()
print(f"当前鼠标位置: ({x}, {y})")

relative_x = x / screen_width * 100
relative_y = y / screen_height * 100
print(f"相对位置: 水平 {relative_x:.1f}%, 垂直 {relative_y:.1f}%")

# 保存当前鼠标位置
current_x, current_y = pyautogui.position()
pyautogui.click(button='right')
# 恢复鼠标位置
pyautogui.moveTo(current_x, current_y)

print(f"右键点击完成！点击位置: ({x}, {y})")
