import csv
import time
import re
from aliyunsdkcore.client import AcsClient
from aliyunsdkalimt.request.v20181012.TranslateGeneralRequest import TranslateGeneralRequest

# 请将此处替换为你的阿里云AK/SK
access_key_id = ''
access_secret = ''
REGION_ID = 'cn-hangzhou'

# 初始化AcsClient
if not access_key_id or not access_secret:
    raise ValueError('请设置有效的阿里云AccessKey ID和Secret')

client = AcsClient(access_key_id, access_secret, REGION_ID)


def aliyun_translate(text, from_lang='en', to_lang='zh'):
    # 分割文本与占位符
    parts = re.split(r'($[^]]+$)', text)
    translated_parts = []
    
    for part in parts:
        if re.match(r'$$[^]]+$$', part):
            # 是 [xxx] 占位符，直接保留
            translated_parts.append(part)
        elif part.strip():
            # 非空文本，进行翻译
            request = TranslateGeneralRequest()
            request.set_SourceLanguage(from_lang)
            request.set_TargetLanguage(to_lang)
            request.set_SourceText(part)
            request.set_FormatType('text')
            try:
                response = client.do_action_with_exception(request)
                response_str = str(response, encoding='utf-8')
                print(f"[调试] 翻译API返回：{response_str}")
                import json
                result = json.loads(response_str)
                zh = result.get('Data', {}).get('Translated', '')
                translated_parts.append(zh)
            except Exception as e:
                print('翻译失败:', e)
                translated_parts.append(part)
        else:
            # 空内容，直接保留
            translated_parts.append(part)

    return ''.join(translated_parts)
    
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