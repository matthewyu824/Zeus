from docx import Document
import json

def is_title(paragraph):
    """判断一个段落是否是标题"""
    text = paragraph.text.strip()
    
    for run in paragraph.runs:
        if not run.text.strip():
            continue
        
        font_size = None
        if run.font.size:
            font_size = run.font.size.pt
        elif run.style and run.style.font and run.style.font.size:
            font_size = run.style.font.size.pt
        
        is_bold = run.font.bold
        
        style_name = ""
        if paragraph.style:
            style_name = paragraph.style.name.lower()
        
        if 'heading' in style_name or 'title' in style_name:
            return True
        elif font_size and font_size > 12:
            return True
        elif is_bold:
            return True
        elif text.endswith('：') or text.endswith(':'):
            return True
    
    return False

def process_document(docx_path):
    """处理Word文档，生成三级分类结构"""
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
        
        if is_title(paragraph):
            if text.endswith('：') or text.endswith(':'):
                category_name = text[:-1]
                if current_level1:
                    if category_name not in result[current_level1]:
                        result[current_level1][category_name] = []
                    current_level2 = category_name
                    print(f"  二级分类: {category_name}")
                else:
                    if text not in result:
                        result[text] = {}
                    current_level1 = text
                    current_level2 = None
                    print(f"一级分类: {text}")
            else:
                if text not in result:
                    result[text] = {}
                current_level1 = text
                current_level2 = None
                print(f"一级分类: {text}")
        else:
            if current_level1 and current_level2:
                result[current_level1][current_level2].append(text)
                print(f"    三级内容: {text}")
            elif current_level1:
                if '其他' not in result[current_level1]:
                    result[current_level1]['其他'] = []
                result[current_level1]['其他'].append(text)
                print(f"    三级内容(其他): {text}")
    
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
    
    data = process_document(docx_path)
    
    if data:
        save_to_json(data, output_file)
    else:
        print("处理失败")

if __name__ == '__main__':
    main()
