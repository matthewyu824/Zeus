import json

def convert_txt_to_json(input_file, output_file):
    result = {}
    current_main_category = None
    current_sub_category = None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith('###'):
                current_main_category = line[3:]
                result[current_main_category] = {}
                current_sub_category = None
            elif line.endswith('：'):
                current_sub_category = line[:-1]
                if current_main_category and current_sub_category:
                    result[current_main_category][current_sub_category] = []
            else:
                if current_main_category and current_sub_category:
                    result[current_main_category][current_sub_category].append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"转换完成！共 {len(result)} 个一级分类")
    for main_category, sub_categories in result.items():
        total_scripts = sum(len(scripts) for scripts in sub_categories.values())
        print(f"  {main_category}: {len(sub_categories)} 个二级分类, 共 {total_scripts} 条话术")
        for sub_category, scripts in sub_categories.items():
            print(f"    - {sub_category}: {len(scripts)} 条")

if __name__ == '__main__':
    input_file = '水军话术.txt'
    output_file = '话术.json'
    convert_txt_to_json(input_file, output_file)
