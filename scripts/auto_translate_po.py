#!/usr/bin/env python3
"""
auto_translate_po.py - 自动翻译 .po 文件中的未翻译条目

用法:
    python auto_translate_po.py <po_file_path> [--provider deepl|anthropic]

环境变量:
    DEEPL_API_KEY      DeepL API Key（必需，当 provider=deepl）
    ANTHROPIC_API_KEY  Anthropic API Key（必需，当 provider=anthropic）
    TRANSLATE_TARGET   目标语言代码，默认 zh_CN（简体中文）或 zh_TW（繁体中文）
"""

import sys
import os
import re
import time
from pathlib import Path


def read_po_file(po_path):
    """读取 .po 文件，返回 msgid -> msgstr 字典和原始内容列表"""
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    comment_lines = []

    for line in lines:
        stripped = line.rstrip('\n')

        # 收集注释/元数据行
        if stripped.startswith('#'):
            comment_lines.append(stripped)
            continue

        # 遇到空行，保存之前的条目
        if stripped == '':
            if current_msgid is not None:
                entries.append({
                    'msgid': current_msgid,
                    'msgstr': current_msgstr,
                    'comments': comment_lines[:],
                })
                current_msgid = None
                current_msgstr = None
                comment_lines = []
            continue

        # 解析 msgid
        if stripped.startswith('msgid '):
            # 如果之前有未保存的条目，先保存
            if current_msgid is not None:
                entries.append({
                    'msgid': current_msgid,
                    'msgstr': current_msgstr,
                    'comments': comment_lines[:],
                })
            current_msgid = stripped[6:].strip('"')
            current_msgstr = None
            in_msgid = True
            in_msgstr = False
            comment_lines = []
        elif stripped.startswith('msgstr '):
            current_msgstr = stripped[7:].strip('"')
            in_msgid = False
            in_msgstr = True
        elif stripped.startswith('"') and (in_msgid or in_msgstr):
            # 多行字符串 continuation
            content = stripped.strip('"')
            if in_msgid and current_msgid is not None:
                current_msgid += content
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += content

    # 保存最后一个条目
    if current_msgid is not None:
        entries.append({
            'msgid': current_msgid,
            'msgstr': current_msgstr,
            'comments': comment_lines[:],
        })

    return entries, lines


def translate_with_deepl(text, api_key, target_lang='ZH'):
    """使用 DeepL API 翻译文本"""
    import urllib.request
    import json

    url = 'https://api-free.deepl.com/v2/translate'
    data = {
        'text': [text],
        'target_lang': target_lang,
        'tag_handling': 'html',  # 保留 HTML 标签
    }

    req = urllib.request.Request(url)
    req.add_header('Authorization', f'DeepL-Auth-Key {api_key}')
    req.add_header('Content-Type', 'application/json')

    payload = json.dumps(data).encode('utf-8')
    response = urllib.request.urlopen(req, payload)
    result = json.loads(response.read().decode('utf-8'))

    return result['translations'][0]['text']


def translate_with_anthropic(text, api_key, target_lang='Simplified Chinese'):
    """使用 Anthropic (Claude) API 翻译文本"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Translate the following English text to {target_lang}. Preserve any HTML tags, placeholders like %(name)s, {{% trans %}}, and special characters exactly as they are. Only output the translated text, nothing else.

Text: "{text}"

Translation:"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return message.content[0].text.strip()


def get_target_language(locale_code):
    """根据 locale 代码返回翻译 API 的目标语言"""
    lang_map = {
        'zh_Hans_CN': 'ZH',       # DeepL: ZH (Simplified)
        'zh_Hant_TW': 'ZH-TW',    # DeepL: ZH-TW (Traditional)
        'ja': 'JA',
        'ko': 'KO',
        'fr': 'FR',
        'de': 'DE',
        'es': 'ES',
    }
    return lang_map.get(locale_code, 'ZH')


def auto_translate_entries(entries, provider='deepl', locale='zh_Hans_CN'):
    """自动翻译所有 msgstr 为空的条目"""
    api_key_env = 'DEEPL_API_KEY' if provider == 'deepl' else 'ANTHROPIC_API_KEY'
    api_key = os.environ.get(api_key_env)

    if not api_key:
        print(f"警告: 未设置 {api_key_env}，跳过自动翻译")
        return 0

    target_lang = get_target_language(locale)
    anthropic_target = 'Simplified Chinese' if locale == 'zh_Hans_CN' else 'Traditional Chinese'

    translated_count = 0
    total_untranslated = sum(1 for e in entries if not e['msgstr'] and e['msgid'])

    print(f"找到 {total_untranslated} 条未翻译字符串")

    for i, entry in enumerate(entries):
        if not entry['msgstr'] and entry['msgid']:
            msgid = entry['msgid'].replace('\\n', '\n').replace('\\"', '"')

            # 跳过复数形式（plural forms）— Babel 会处理
            if msgid.startswith('(') or msgid.endswith(')'):
                continue

            try:
                if provider == 'deepl':
                    translated = translate_with_deepl(msgid, api_key, target_lang)
                else:
                    translated = translate_with_anthropic(msgid, api_key, anthropic_target)

                # 清理翻译结果
                translated = translated.strip().strip('"').replace('\n', '\\n').replace('"', '\\"')
                entry['msgstr'] = translated
                translated_count += 1
                print(f"  [{i+1}/{len(entries)}] ✓ {msgid[:50]}... → {translated[:30]}...")

                # API 速率限制：每次请求后等待
                time.sleep(0.5)

            except Exception as e:
                print(f"  [{i+1}/{len(entries)}] ✗ 翻译失败: {e}")
                print(f"     原文: {msgid[:80]}")

    print(f"\n完成: {translated_count}/{total_untranslated} 条已翻译")
    return translated_count


def write_po_file(po_path, entries, original_lines):
    """将翻译后的条目写回 .po 文件"""
    output_lines = []

    for entry in entries:
        # 写入注释
        for comment in entry['comments']:
            output_lines.append(comment + '\n')

        # 写入 msgid
        if '\n' in entry['msgid']:
            output_lines.append(f'msgid ""\n')
            output_lines.append(f'"{entry["msgid"]}"\n')
        else:
            output_lines.append(f'msgid "{entry["msgid"]}"\n')

        # 写入 msgstr
        if '\n' in entry['msgstr']:
            output_lines.append(f'msgstr ""\n')
            output_lines.append(f'"{entry["msgstr"]}"\n')
        else:
            output_lines.append(f'msgstr "{entry["msgstr"]}"\n')

        output_lines.append('\n')

    with open(po_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"已写入 {po_path} ({len(entries)} 个条目)")


def main():
    if len(sys.argv) < 2:
        print("用法: python auto_translate_po.py <po_file_path> [--provider deepl|anthropic]")
        sys.exit(1)

    po_path = sys.argv[1]
    provider = 'deepl'
    if '--provider' in sys.argv:
        idx = sys.argv.index('--provider')
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]

    if not os.path.exists(po_path):
        print(f"错误: 文件不存在: {po_path}")
        sys.exit(1)

    # 从路径推断 locale
    path_parts = Path(po_path).parts
    locale = 'zh_Hans_CN'
    for part in path_parts:
        if part in ('zh_Hans_CN', 'zh_Hant_TW', 'ja', 'ko', 'fr', 'de', 'es'):
            locale = part
            break

    print(f"处理文件: {po_path}")
    print(f"Locale: {locale}")
    print(f"翻译提供商: {provider}")

    entries, original_lines = read_po_file(po_path)
    count = auto_translate_entries(entries, provider=provider, locale=locale)

    if count > 0:
        write_po_file(po_path, entries, original_lines)
        print(f"✓ 成功翻译 {count} 条")
    else:
        print("没有需要翻译的新字符串")


if __name__ == '__main__':
    main()
