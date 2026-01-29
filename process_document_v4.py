from docx import Document
import json

def process_document_by_style(docx_path):
    """根据样式名称处理Word文档，生成三级分类结构"""
    print(f"正在处理文档: {docx_path}")
    print("=" * 60)
    
    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"读取文档失败: {e}")
        return None
    
    result = {}
    current_level1 = None
    current_level2 = None
    
    for para_idx, paragraph in enumerate(doc.paragraphs):
        if not paragraph.text.strip():
            continue
        
        text = paragraph.text.strip()
        
        style_name = ""
        if paragraph.style:
            style_name = paragraph.style.name
        
        if style_name == "Heading 2":
            if text not in result:
                result[text] = {}
            current_level1 = text
            current_level2 = None
            print(f"一级分类(Heading 2): {text}")
        elif style_name == "Heading 5":
            if current_level1:
                if text not in result[current_level1]:
                    result[current_level1][text] = []
                current_level2 = text
                print(f"  二级分类(Heading 5): {text}")
            else:
                if text not in result:
                    result[text] = {}
                current_level1 = text
                current_level2 = None
                print(f"一级分类(Heading 2): {text}")
        elif style_name == "Normal":
            if current_level1 and current_level2:
                result[current_level1][current_level2].append(text)
                print(f"    三级内容(Normal): {text}")
            elif current_level1:
                if '其他' not in result[current_level1]:
                    result[current_level1]['其他'] = []
                result[current_level1]['其他'].append(text)
                print(f"    三级内容(Normal-其他): {text}")
    
    print("\n" + "=" * 60)
    print(f"处理完成！共 {len(result)} 个一级分类")
    for level1, level2_dict in result.items():
        total_items = sum(len(items) for items in level2_dict.values())
        print(f"  {level1}: {len(level2_dict)} 个二级分类, 共 {total_items} 条内容")
    print("=" * 60)
    
    return result

def save_to_json(data, output_file):
    """保存结果到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")

def main():
    """主函数"""
    docx_path = "水军话术(2).docx"
    output_file = "水军话术分类.json"
    
    data = process_document_by_style(docx_path)
    
    if data:
        save_to_json(data, output_file)
    else:
        print("处理失败")

if __name__ == '__main__':
    main()
