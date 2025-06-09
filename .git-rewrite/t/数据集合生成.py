import os
import re
import csv

def find_xml_files(root):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.xml'):
                yield os.path.join(dirpath, filename)

def extract_pairs_from_file(filepath):
    pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    en = None
    for line in lines:
        en_match = re.match(r'\s*<!--\s*EN:\s*(.*?)\s*-->', line)
        zh_match = re.match(r'\s*<[^>]+>(.*?)</[^>]+>', line)
        if en_match:
            en = en_match.group(1).strip()
        elif en and zh_match:
            zh = zh_match.group(1).strip()
            if en and zh and en != zh:
                pairs.append([en, zh])
            en = None
        else:
            en = None
    return pairs

def main():
    output_path = 'parallel_corpus.csv'
    all_pairs = []
    seen = set()
    # 遍历当前目录及所有子目录
    for xml_file in find_xml_files('.'):
        pairs = extract_pairs_from_file(xml_file)
        for en, zh in pairs:
            key = (en, zh)
            if key not in seen:
                all_pairs.append([en, zh])
                seen.add(key)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for en, zh in all_pairs:
            writer.writerow([en, zh])
    print(f'已生成 {output_path}，共{len(all_pairs)} 条中英对。')

if __name__ == '__main__':
    main()