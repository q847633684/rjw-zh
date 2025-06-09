import os
import csv
import xml.etree.ElementTree as ET

def import_csv_to_xml(csv_file_path, xml_folder_path):
    """
    将CSV文件中的翻译导入到XML文件中
    :param csv_file_path: CSV文件路径
    :param xml_folder_path: XML文件夹路径
    
    """
    try:
        # 读取CSV文件
        translations = {}
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # 检查CSV文件的字段名
            fieldnames = reader.fieldnames
            print(f"🔍 CSV文件字段: {fieldnames}")
            
            # 确定使用哪个字段作为翻译键
            key_field = 'Key'  # 默认字段
            translation_field = '翻译'  # 默认翻译字段
            
            # 如果包含三个字段（Key、Original Text、翻译）
            if len(fieldnames) >= 3:
                key_field = fieldnames[0]
                translation_field = fieldnames[2]
            
            for row in reader:
                # 使用指定的字段作为键，翻译字段作为值
                if key_field in row and translation_field in row:
                    translations[row[key_field]] = row[translation_field]

        # 遍历XML文件夹中的所有XML文件
        for root_dir, _, files in os.walk(xml_folder_path):
            for file in files:
                if not file.endswith(".xml"):
                    continue

                file_path = os.path.join(root_dir, file)
                print(f"🔄 开始处理XML文件: {file_path}")
                
                try:
                    tree = ET.parse(file_path)
                    root_elem = tree.getroot()
                    
                    # 记录当前文件的更新情况
                    updated_elements = 0
                    skipped_elements = 0
                    matched_by_tag = 0
                    matched_by_text = 0
                    
                    # 遍历XML中的所有元素
                    for elem in root_elem.iter():
                        # 如果元素文本存在且不是空白
                        if elem.text and elem.text.strip():
                            key = elem.tag
                            # 如果元素的tag在翻译字典中
                            if key in translations:
                                # 更新文本内容
                                old_text = elem.text
                                elem.text = translations[key]
                                updated_elements += 1
                                matched_by_tag += 1
                                print(f"📝 替换成功 (by tag): {old_text} -> {elem.text}")
                            # 否则尝试用文本内容作为键
                            elif elem.text.strip() in translations:
                                old_text = elem.text
                                elem.text = translations[elem.text.strip()]
                                updated_elements += 1
                                matched_by_text += 1
                                print(f"📝 替换成功 (by text): {old_text} -> {elem.text}")
                            else:
                                skipped_elements += 1
                                print(f"🔸 未找到匹配的翻译: {elem.text.strip()}")

                    # 保存修改后的XML文件
                    tree.write(file_path, encoding="utf-8", xml_declaration=True, method="xml", short_empty_elements=False)
                    print(f"✅ 完成XML文件更新: {file_path}")
                    print(f"📊 更新统计 - 总替换: {updated_elements}, 通过tag替换: {matched_by_tag}, 通过文本替换: {matched_by_text}, 未替换: {skipped_elements}")

                except ET.ParseError as e:
                    print(f"⚠️ 解析XML失败: {file_path}, 错误: {str(e)}")
                    continue

    except Exception as e:
        print(f"❌ 导入CSV到XML失败: {str(e)}")

if __name__ == "__main__":
    # ====== 测试用写死路径（适合调试）======
    csv_file_path = r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\rjw-zh\RJW\1.5\rjw_Translation\Languages\ChineseSimplified\translations_zh.csv"
    xml_folder_path = r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\rjw-zh\RJW\1.5\rjw_Translation\Languages\ChineseSimplified\DefInjected"
    
    # 执行CSV到XML的导入
    import_csv_to_xml(csv_file_path, xml_folder_path)
