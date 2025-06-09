import os
import sys
import csv
import xml.etree.ElementTree as ET

def find_versioned_subdir(base_path, target_version="1.5"):
    """查找指定版本号的子目录（如 1.5）"""
    if not os.path.exists(base_path):
        return None
    
    version_dir = os.path.join(base_path, target_version)
    if os.path.isdir(version_dir):
        return version_dir
    
    print(f"⚠️ 指定版本目录不存在: {version_dir}")
    return None


def create_translation_mod(original_mod_path, output_path, language="ChineseSimplified"):
    mod_name = os.path.basename(original_mod_path)
    translation_mod_path = os.path.join(output_path, f"{mod_name}_Translation")
    lang_dir = os.path.join(translation_mod_path, "Languages", language)

    # 创建目录结构
    os.makedirs(os.path.join(lang_dir, "DefInjected"), exist_ok=True)
    os.makedirs(os.path.join(lang_dir, "Keyed"), exist_ok=True)
    os.makedirs(os.path.join(translation_mod_path, "About"), exist_ok=True)

    # 写 About.xml
    about_path = os.path.join(translation_mod_path, "About", "About.xml")
    with open(about_path, "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>{mod_name} Translation ({language})</name>
    <author>YourName</author>
    <packageId>{mod_name.lower()}.translation.{language.lower()}</packageId>
    <supportedVersions><li>1.5</li></supportedVersions>
    <description>Translation for {mod_name} in {language}</description>
    <modDependencies>
        <li>
            <packageId>{mod_name.lower()}</packageId>
            <displayName>{mod_name}</displayName>
        </li>
    </modDependencies>
</ModMetaData>
""")
    print(f"✅ Created About.xml at {about_path}")

    # 写 LanguageData.xml
    language_data_path = os.path.join(lang_dir, "LanguageData.xml")
    root = ET.Element("LanguageData")
    ET.SubElement(root, "languageNativeName").text = "简体中文"
    ET.SubElement(root, "languageEnglishName").text = "ChineseSimplified"
    ET.SubElement(root, "friendlyNameNative").text = "简体中文"
    ET.SubElement(root, "friendlyNameEnglish").text = "ChineseSimplified"
    tree = ET.ElementTree(root)
    tree.write(language_data_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Created LanguageData.xml at {language_data_path}")

    # 可翻译标签列表
    translatable_tags = [
        "label", "description", "labelNoun", "gerund", "gerundLabel", "verb", "helpText", "text",
        "labelShort", "pawnLabel", "labelPlural", "descriptionShort", "textFemale",
        "textMale", "reportString", "labelAbstract", "baseDesc", "title", "titleShort"
    ]

    keyed_translations = []
    csv_entries = []

    # 自动判断是否需要进入版本号目录（强制使用 1.5）
    def_base_path = original_mod_path
    keyed_base_path = original_mod_path

    versioned_dir = find_versioned_subdir(original_mod_path, target_version="1.5")
    if versioned_dir:
        def_base_path = versioned_dir
        keyed_base_path = versioned_dir

    # ========== DefInjected 处理 ==========
    defs_path = os.path.join(def_base_path, "Defs")
    if os.path.exists(defs_path):
        for root_dir, _, files in os.walk(defs_path):
            for file in files:
                if not file.endswith(".xml"):
                    continue
                file_path = os.path.join(root_dir, file)
                try:
                    tree = ET.parse(file_path)
                    root_elem = tree.getroot()

                    base_name = os.path.splitext(file)[0]
                    rel_path = os.path.relpath(root_dir, defs_path)
                    out_dir = os.path.join(lang_dir, "DefInjected", rel_path)

                    xml_content = []
                    has_translation = False

                    # 遍历所有带有 defName 或 Name 的节点
                    for def_elem in list(root_elem.findall("*[defName]")) + list(root_elem.findall("*[@Name]")):
                        # 提取 defName 或 Name 属性作为 key 前缀
                        def_name_elem = def_elem.find("defName")
                        if def_name_elem is not None and def_name_elem.text and def_name_elem.text.strip():
                            def_name = def_name_elem.text.strip()
                        elif 'Name' in def_elem.attrib:
                            def_name = def_elem.attrib['Name']
                        else:
                            continue

                        li_indices = {}  # 每个 Def 独立索引
                        parent_tag_stack = []  # 每个 Def 独立父标签栈
                        extracted_keys = set()  # 记录已提取的 key
                        inside_li = False  # 是否正在处理 li 标签
                        current_parent = None  # 当前父标签
                        has_translatable_content = False  # 当前li是否有可翻译内容

                        # 提取该 Def 下的可翻译内容
                        for elem in def_elem.iter():
                            # 处理li标签
                            if elem.tag == "li" and len(parent_tag_stack) > 0:
                                current_parent = parent_tag_stack[-1]
                                if current_parent not in li_indices:
                                    li_indices[current_parent] = -1
                                li_indices[current_parent] += 1

                            # 处理stages标签
                            elif elem.tag == "stages":
                                parent_tag_stack.append("stages")
                                stage_index = -1  # 初始化索引为-1

                            elif elem.tag == "label" and parent_tag_stack and parent_tag_stack[-1] == "stages":
                                stage_index += 1  # 遇到label才递增索引
                                key = f"{def_name}.stages.{stage_index}.label"
                                value = elem.text.strip()
                                if key not in extracted_keys:
                                    xml_content.append(f"    <{key}>{value}</{key}>")
                                    csv_entries.append([key, value])
                                    has_translation = True
                                    extracted_keys.add(key)

                            # 提取可翻译内容
                            elif elem.tag in translatable_tags and elem.text and elem.text.strip():
                                # 如果是父标签下的li元素
                                if parent_tag_stack and elem.tag in translatable_tags:
                                    parent = parent_tag_stack[-1]
                                    # 确保parent存在于li_indices中
                                    if parent in li_indices and li_indices[parent] >= 0:
                                        index = li_indices[parent]
                                        key = f"{def_name}.{parent}.{index}.{elem.tag}"
                                    else:
                                        key = f"{def_name}.{elem.tag}"
                                else:
                                    key = f"{def_name}.{elem.tag}"

                                value = elem.text.strip()

                                if key in extracted_keys:
                                    continue  # 跳过重复 key

                                xml_content.append(f"    <{key}>{value}</{key}>")
                                csv_entries.append([key, value])
                                has_translation = True
                                extracted_keys.add(key)
                                
                                # 标记当前li有可翻译内容
                                has_translatable_content = True

                            # 如果当前li没有可翻译内容，则回退索引
                            if inside_li and not has_translatable_content and current_parent:
                                li_indices[current_parent] -= 1

                    # 有内容才写入文件
                    if has_translation:
                        os.makedirs(out_dir, exist_ok=True)
                        out_file_xml = os.path.join(out_dir, f"{base_name}.xml")
                        with open(out_file_xml, "w", encoding="utf-8") as xml_out:
                            xml_out.write('<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n')
                            xml_out.write('\n'.join(xml_content))
                            xml_out.write('\n</LanguageData>\n')
                        print(f"✅ 已创建翻译文件: {out_file_xml}")
                    else:
                        print(f"🔸 未找到可翻译内容，跳过文件: {file_path}")

                # 在处理XML文件时，建议添加更多错误处理逻辑
                except ET.ParseError as e:
                    print(f"⚠️ 解析XML失败: {file_path}, 错误: {str(e)}")
                    continue
    else:
        print(f"⚠️ Defs 路径不存在: {defs_path}")

    # ========== Keyed 处理 ==========
    keyed_path = os.path.join(keyed_base_path, "Languages", "English", "Keyed")
    if os.path.exists(keyed_path):
        for root_dir, _, files in os.walk(keyed_path):
            for file in files:
                if not file.endswith(".xml"):
                    continue
                file_path = os.path.join(root_dir, file)
                try:
                    tree = ET.parse(file_path)
                    for elem in tree.getroot():
                        if elem.text and elem.text.strip():
                            key = elem.tag
                            value = elem.text.strip()
                            keyed_translations.append((key, value))
                            csv_entries.append([key, value])
                except ET.ParseError:
                    print(f"⚠️ 解析XML失败: {file_path}")
    else:
        print(f"⚠️ Keyed 路径不存在: {keyed_path}")

    # ========== 输出 Keyed 文件 ==========
    if keyed_translations:
        out_file_xml = os.path.join(lang_dir, "Keyed", "Keys.xml")
        with open(out_file_xml, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n')
            for key, value in keyed_translations:
                f.write(f"    <{key}>{value}</{key}>\n")
            f.write('</LanguageData>\n')
        print(f"✅ 创建的键文件: {out_file_xml}")

    # ========== 输出 CSV 文件 ==========
    if csv_entries:
        csv_path = os.path.join(lang_dir, "translations.csv")
        with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Key', 'Original Text'])
            for key, value in csv_entries:
                writer.writerow([key, value])
        print(f"✅ 创建的CSV翻译文件: {csv_path}")


if __name__ == "__main__":
    # ====== 测试用写死路径（适合调试）======
    original_mod_path = r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\rjw"
    output_path = r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\rjw-zh\RJW\1.5"

    create_translation_mod(original_mod_path, output_path)