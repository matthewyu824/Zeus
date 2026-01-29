import os

folder_path = '话术文件'

# 获取所有文件并按名称排序
files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

counter = 1
for file_name in files:
    new_name = f'{counter:03d}_{file_name}'
    old_path = os.path.join(folder_path, file_name)
    new_path = os.path.join(folder_path, new_name)
    os.rename(old_path, new_path)
    print(f'重命名: {file_name} -> {new_name}')
    counter += 1

print('重命名完成！')