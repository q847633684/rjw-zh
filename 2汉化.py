import csv
import time
import re
from aliyunsdkcore.client import AcsClient
from aliyunsdkalimt.request.v20181012.TranslateGeneralRequest import TranslateGeneralRequest

# 请将此处替换为你的阿里云AK/SK
access_key_id = ''
access_secret = ''
REGION_ID = 'cn-hangzhou'

client = AcsClient(
    access_key_id,
    access_secret,
    REGION_ID
)

def replace_placeholders(text):
    # 匹配所有 [xxx] 占位符
    pattern = re.compile(r'(\[[^\]]+\])')
    placeholders = pattern.findall(text)
    replaced = text
    mapping = {}
    for idx, ph in enumerate(placeholders):
        key = f'__PLACEHOLDER_{idx}__'
        replaced = replaced.replace(ph, key)
        mapping[key] = ph
    return replaced, mapping

def restore_placeholders(text, mapping):
    for key, ph in mapping.items():
        text = text.replace(key, ph)
    return text

def aliyun_translate(text, from_lang='en', to_lang='zh'):
    # 只翻译非全占位符内容
    replaced, mapping = replace_placeholders(text)
    request = TranslateGeneralRequest()
    request.set_SourceLanguage(from_lang)
    request.set_TargetLanguage(to_lang)
    request.set_SourceText(replaced)
    request.set_FormatType('text')
    try:
        response = client.do_action_with_exception(request)
        response_str = str(response, encoding='utf-8')
        print(f"[调试] 翻译API返回：{response_str}")
        import json
        result = json.loads(response_str)
        zh = result.get('Data', {}).get('Translated', '')
        zh = restore_placeholders(zh, mapping)
        return zh
    except Exception as e:
        print('翻译失败:', e)
        return text
    
def translate_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        header = next(reader)
        writer.writerow(header + ['翻译'])
        line_num = 1
        for row in reader:
            key, text = row[0], row[1]
            # 跳过空行、空key、空文本
            if text.strip() == '' or key.strip() == '':
                writer.writerow(row + [''])
                print(f"[调试] 跳过第{line_num}行：{row}")
                line_num += 1
                continue
            # 如果内容全是占位符，直接写入原文
            if re.fullmatch(r'(\s*\[[^\]]+\]\s*)+', text):
                writer.writerow(row + [text])
                print(f"[调试] 跳过第{line_num}行（全占位符不翻译）：{text}")
                line_num += 1
                continue
            zh = aliyun_translate(text)
            if not zh or zh.strip() == '':
                print(f"[调试] 第{line_num}行翻译失败，已暂停。原文：{text}  翻译：{zh}")
                break
            if zh == text:
                print(f"[调试] 第{line_num}行未翻译，原文写入。原文：{text}")
                writer.writerow(row + [zh])
                line_num += 1
                time.sleep(0.5)
                continue
            writer.writerow(row + [zh])
            print(f"[调试] 第{line_num}行翻译完成：原文：{text}  =>  翻译：{zh}")
            line_num += 1
            time.sleep(0.5)  # 防止QPS超限

if __name__ == '__main__':
    translate_csv(
        r'RJW/1.5/rjw_Translation/Languages/ChineseSimplified/translations.csv',
        r'RJW/1.5/rjw_Translation/Languages/ChineseSimplified/translations_zh.csv'
    )
    