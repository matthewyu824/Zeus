import json
import os

def split_json_by_level1(input_file, output_dir='./分类文件'):
    """根据一级分类将JSON文件分割成多个小文件"""
    print(f"正在读取文件: {input_file}")
    print("=" * 60)
    
    if not os.path.exists(input_file):
        print(f"文件不存在: {input_file}")
        return
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    total_files = 0
    
    for level1, content in data.items():
        filename = f"{level1}.json"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            total_files += 1
            print(f"✓ 已生成: {filename}")
        except Exception as e:
            print(f"✗ 生成文件失败 {filename}: {e}")
    
    print("\n" + "=" * 60)
    print(f"分割完成！共生成 {total_files} 个文件")
    print(f"文件已保存到: {output_dir}")
    print("=" * 60)

def main():
    """主函数"""
    input_file = "水军话术分类.json"
    split_json_by_level1(input_file)

if __name__ == '__main__':
    main()
