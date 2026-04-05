#!/usr/bin/env python3
"""
auto_translate_po.py - 自动翻译 .po 文件中的未翻译条目

用法:
    python auto_translate_po.py <po_file_path> [--provider <provider>]

支持的 provider:
    deepl    DeepL API，通过 DEEPL_API_URL 自定义端点
    openai   OpenAI 兼容接口（SiliconFlow、本地 LLM 等），通过 OPENAI_API_URL 自定义

环境变量（在 GitHub Actions Secrets / Variables 中配置）:

    DEEPL_API_KEY    DeepL API Key（Secrets）
    DEEPL_API_URL    DeepL 端点（Variables，可选）
                     默认（免费版）: https://api-free.deepl.com/v2/translate
                     Pro 版:        https://api.deepl.com/v2/translate

    OPENAI_API_KEY   OpenAI 兼容 API Key（Secrets）
    OPENAI_API_URL   API 端点（Variables，可选）
                     默认: https://api.openai.com/v1/chat/completions
                     SiliconFlow: https://api.siliconflow.cn/v1/chat/completions
    OPENAI_MODEL     模型名（Variables，可选）
                     默认: gpt-4o-mini
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path


# ── 默认端点 ──────────────────────────────────────────────────────────────────
DEFAULT_DEEPL_URL    = 'https://api-free.deepl.com/v2/translate'
DEFAULT_OPENAI_URL   = 'https://api.openai.com/v1/chat/completions'
DEFAULT_OPENAI_MODEL = 'gpt-4o-mini'


# ── 语言代码映射 ──────────────────────────────────────────────────────────────
DEEPL_LANG_MAP = {
    'zh_Hans_CN': 'ZH',
    'zh_Hant_TW': 'ZH-TW',
    'ja': 'JA', 'ko': 'KO', 'fr': 'FR',
    'de': 'DE', 'es': 'ES', 'ru': 'RU',
    'pt_BR': 'PT-BR', 'ar': 'AR', 'it': 'IT',
}

HUMAN_LANG_MAP = {
    'zh_Hans_CN': 'Simplified Chinese',
    'zh_Hant_TW': 'Traditional Chinese',
    'ja': 'Japanese', 'ko': 'Korean', 'fr': 'French',
    'de': 'German', 'es': 'Spanish', 'ru': 'Russian',
    'pt_BR': 'Brazilian Portuguese', 'ar': 'Arabic', 'it': 'Italian',
}


# ── .po 文件读写 ──────────────────────────────────────────────────────────────
def read_po_file(po_path):
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    for block in content.split('\n\n'):
        lines = block.strip().splitlines()
        if not lines:
            continue

        msgid = msgstr = None
        raw_before = []
        in_msgid = in_msgstr = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('msgid '):
                if msgid is not None:
                    entries.append({'msgid': msgid, 'msgstr': msgstr, 'raw_before': raw_before})
                msgid = _parse_po_string(line[6:])
                msgstr = None
                in_msgid, in_msgstr = True, False
                raw_before = []
            elif line.startswith('msgstr '):
                msgstr = _parse_po_string(line[7:])
                in_msgid, in_msgstr = False, True
            elif line.startswith('"'):
                if in_msgid:
                    msgid = (msgid or '') + _parse_po_string(line)
                elif in_msgstr:
                    msgstr = (msgstr or '') + _parse_po_string(line)
            else:
                raw_before.append(line)
            i += 1

        if msgid is not None:
            entries.append({'msgid': msgid, 'msgstr': msgstr, 'raw_before': raw_before})

    return entries


def _parse_po_string(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def _encode_po_string(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def write_po_file(po_path, entries):
    lines = []
    for entry in entries:
        for raw_line in entry['raw_before']:
            lines.append(raw_line)
        lines.append(f'msgid "{_encode_po_string(entry["msgid"])}"')
        lines.append(f'msgstr "{_encode_po_string(entry["msgstr"] or "")}"')
        lines.append('')
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ── HTTP 工具 ─────────────────────────────────────────────────────────────────
def _http_post(url, headers, data):
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from e


# ── 翻译后端 ──────────────────────────────────────────────────────────────────
def translate_deepl(text, api_key, locale):
    url = os.environ.get('DEEPL_API_URL', DEFAULT_DEEPL_URL)
    result = _http_post(
        url,
        headers={
            'Authorization': f'DeepL-Auth-Key {api_key}',
            'Content-Type': 'application/json',
        },
        data={
            'text': [text],
            'target_lang': DEEPL_LANG_MAP.get(locale, 'ZH'),
            'tag_handling': 'html',
        },
    )
    return result['translations'][0]['text']


def translate_openai(text, api_key, locale):
    url   = os.environ.get('OPENAI_API_URL', DEFAULT_OPENAI_URL)
    model = os.environ.get('OPENAI_MODEL',   DEFAULT_OPENAI_MODEL)
    target_lang = HUMAN_LANG_MAP.get(locale, 'Simplified Chinese')

    result = _http_post(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        data={
            'model': model,
            'temperature': 0,
            'max_tokens': 300,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        f'You are a professional UI translator. '
                        f'Translate English strings to {target_lang}. '
                        f'Preserve HTML tags, %(name)s placeholders, and special characters exactly. '
                        f'Output only the translation, no explanation.'
                    ),
                },
                {'role': 'user', 'content': text},
            ],
        },
    )
    return result['choices'][0]['message']['content'].strip()


# ── 主流程 ────────────────────────────────────────────────────────────────────
PROVIDERS = {
    'deepl':  (translate_deepl,  'DEEPL_API_KEY'),
    'openai': (translate_openai, 'OPENAI_API_KEY'),
}


def auto_translate(po_path, provider='deepl'):
    translate_fn, key_env = PROVIDERS.get(provider, (None, None))
    if translate_fn is None:
        print(f"未知 provider: {provider}，支持: {list(PROVIDERS)}")
        sys.exit(1)

    api_key = os.environ.get(key_env)
    if not api_key:
        print(f"未设置 {key_env}，跳过翻译")
        return 0

    locale = 'zh_Hans_CN'
    for part in Path(po_path).parts:
        if part in HUMAN_LANG_MAP:
            locale = part
            break

    if provider == 'deepl':
        endpoint_info = os.environ.get('DEEPL_API_URL', DEFAULT_DEEPL_URL)
    else:
        endpoint_info = (f"{os.environ.get('OPENAI_MODEL', DEFAULT_OPENAI_MODEL)}"
                         f" @ {os.environ.get('OPENAI_API_URL', DEFAULT_OPENAI_URL)}")
    print(f"Locale: {locale}  Provider: {provider}  ({endpoint_info})")

    entries = read_po_file(po_path)
    untranslated = [e for e in entries if not e['msgstr'] and e['msgid']]
    print(f"待翻译: {len(untranslated)}/{len(entries)} 条")

    translated_count = 0
    for i, entry in enumerate(untranslated):
        msgid = entry['msgid']
        try:
            result = translate_fn(msgid, api_key, locale)
            for e in entries:
                if e['msgid'] == msgid and not e['msgstr']:
                    e['msgstr'] = result
                    break
            translated_count += 1
            print(f"  [{i+1}/{len(untranslated)}] ✓ {msgid[:40]!r} → {result[:30]!r}")
            time.sleep(0.3)
        except Exception as exc:
            print(f"  [{i+1}/{len(untranslated)}] ✗ {msgid[:40]!r} — {exc}")

    if translated_count > 0:
        write_po_file(po_path, entries)
        print(f"\n✓ {translated_count}/{len(untranslated)} 条已写入")
    else:
        print("没有新条目被翻译")
    return translated_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    po_path  = sys.argv[1]
    provider = 'deepl'
    if '--provider' in sys.argv:
        idx = sys.argv.index('--provider')
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]

    if not os.path.exists(po_path):
        print(f"错误: 文件不存在: {po_path}")
        sys.exit(1)

    auto_translate(po_path, provider)


if __name__ == '__main__':
    main()


用法:
    python auto_translate_po.py <po_file_path> [--provider <provider>]

支持的 provider:
    deepl       DeepL API（免费版或 Pro 版，通过 DEEPL_API_URL 自定义端点）
    openai      OpenAI 兼容接口（支持 Ollama、SiliconFlow 等，通过 OPENAI_API_URL 自定义）
    anthropic   Anthropic Claude API

环境变量（在 GitHub Actions Secrets 中配置）:
    DEEPL_API_KEY       DeepL API Key
    DEEPL_API_URL       DeepL API 端点（可选）
                        默认: https://api-free.deepl.com/v2/translate
                        Pro 版: https://api.deepl.com/v2/translate

    OPENAI_API_KEY      OpenAI 兼容 API Key
    OPENAI_API_URL      OpenAI 兼容 API 端点（可选）
                        默认: https://api.openai.com/v1/chat/completions
                        Ollama:      http://localhost:11434/v1/chat/completions
                        SiliconFlow: https://api.siliconflow.cn/v1/chat/completions
    OPENAI_MODEL        使用的模型名称（可选）
                        默认: gpt-4o-mini

    ANTHROPIC_API_KEY   Anthropic API Key
    ANTHROPIC_API_URL   Anthropic API 端点（可选）
                        默认: https://api.anthropic.com
    ANTHROPIC_MODEL     使用的模型名称（可选）
                        默认: claude-haiku-4-5-20251001
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path


# ── 默认端点（可通过环境变量覆盖）────────────────────────────────────────────
DEFAULT_DEEPL_URL      = 'https://api-free.deepl.com/v2/translate'
DEFAULT_OPENAI_URL     = 'https://api.openai.com/v1/chat/completions'
DEFAULT_OPENAI_MODEL   = 'gpt-4o-mini'
DEFAULT_ANTHROPIC_URL  = 'https://api.anthropic.com'
DEFAULT_ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001'


# ── 语言代码映射 ──────────────────────────────────────────────────────────────
DEEPL_LANG_MAP = {
    'zh_Hans_CN': 'ZH',
    'zh_Hant_TW': 'ZH-TW',
    'ja': 'JA',
    'ko': 'KO',
    'fr': 'FR',
    'de': 'DE',
    'es': 'ES',
    'ru': 'RU',
    'pt_BR': 'PT-BR',
    'ar': 'AR',
    'it': 'IT',
}

HUMAN_LANG_MAP = {
    'zh_Hans_CN': 'Simplified Chinese',
    'zh_Hant_TW': 'Traditional Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'ru': 'Russian',
    'pt_BR': 'Brazilian Portuguese',
    'ar': 'Arabic',
    'it': 'Italian',
}


# ── .po 文件读写 ──────────────────────────────────────────────────────────────
def read_po_file(po_path):
    """解析 .po 文件，返回条目列表。每个条目: {msgid, msgstr, raw_before}"""
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按空行分块
    blocks = content.split('\n\n')
    entries = []

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        msgid = None
        msgstr = None
        raw_before = []  # 注释 / 元数据行

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('msgid '):
                msgid = _parse_po_string(line[6:])
                # 多行 msgid
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid += _parse_po_string(lines[i])
                    i += 1
                continue
            elif line.startswith('msgstr '):
                msgstr = _parse_po_string(line[7:])
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgstr += _parse_po_string(lines[i])
                    i += 1
                continue
            else:
                raw_before.append(line)
            i += 1

        if msgid is not None and msgstr is not None:
            entries.append({
                'msgid': msgid,
                'msgstr': msgstr,
                'raw_before': raw_before,
            })

    return entries


def _parse_po_string(s):
    """去掉 .po 字符串的首尾引号并处理转义"""
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def _encode_po_string(s):
    """将字符串编码回 .po 格式"""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def write_po_file(po_path, entries):
    """将条目写回 .po 文件"""
    lines = []
    for entry in entries:
        for raw_line in entry['raw_before']:
            lines.append(raw_line)
        lines.append(f'msgid "{_encode_po_string(entry["msgid"])}"')
        lines.append(f'msgstr "{_encode_po_string(entry["msgstr"])}"')
        lines.append('')

    with open(po_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ── 翻译后端 ──────────────────────────────────────────────────────────────────
def _http_post(url, headers, data):
    """通用 HTTP POST，返回解析后的 JSON"""
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f"HTTP {e.code}: {body[:200]}") from e


def translate_deepl(text, api_key, locale):
    """DeepL API 翻译"""
    url = os.environ.get('DEEPL_API_URL', DEFAULT_DEEPL_URL)
    target_lang = DEEPL_LANG_MAP.get(locale, 'ZH')

    result = _http_post(
        url,
        headers={
            'Authorization': f'DeepL-Auth-Key {api_key}',
            'Content-Type': 'application/json',
        },
        data={
            'text': [text],
            'target_lang': target_lang,
            'tag_handling': 'html',
        },
    )
    return result['translations'][0]['text']


def translate_openai(text, api_key, locale):
    """OpenAI 兼容 API 翻译（支持自定义端点）"""
    url   = os.environ.get('OPENAI_API_URL', DEFAULT_OPENAI_URL)
    model = os.environ.get('OPENAI_MODEL',   DEFAULT_OPENAI_MODEL)
    target_lang = HUMAN_LANG_MAP.get(locale, 'Simplified Chinese')

    result = _http_post(
        url,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        data={
            'model': model,
            'temperature': 0,
            'max_tokens': 300,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        f'You are a professional translator. '
                        f'Translate English UI strings to {target_lang}. '
                        f'Preserve HTML tags, placeholders like %(name)s, and special characters exactly. '
                        f'Output only the translated text, nothing else.'
                    ),
                },
                {'role': 'user', 'content': text},
            ],
        },
    )
    return result['choices'][0]['message']['content'].strip()


def translate_anthropic(text, api_key, locale):
    """Anthropic Claude API 翻译（支持自定义端点）"""
    base_url = os.environ.get('ANTHROPIC_API_URL', DEFAULT_ANTHROPIC_URL).rstrip('/')
    model    = os.environ.get('ANTHROPIC_MODEL',   DEFAULT_ANTHROPIC_MODEL)
    target_lang = HUMAN_LANG_MAP.get(locale, 'Simplified Chinese')

    result = _http_post(
        f'{base_url}/v1/messages',
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        },
        data={
            'model': model,
            'max_tokens': 300,
            'temperature': 0,
            'messages': [{
                'role': 'user',
                'content': (
                    f'Translate this English UI string to {target_lang}. '
                    f'Preserve HTML tags, placeholders like %(name)s, and special characters exactly. '
                    f'Output only the translated text:\n\n"{text}"'
                ),
            }],
        },
    )
    return result['content'][0]['text'].strip().strip('"')


# ── 主流程 ────────────────────────────────────────────────────────────────────
TRANSLATE_FN = {
    'deepl':     (translate_deepl,     'DEEPL_API_KEY'),
    'openai':    (translate_openai,    'OPENAI_API_KEY'),
    'anthropic': (translate_anthropic, 'ANTHROPIC_API_KEY'),
}


def auto_translate(po_path, provider='deepl'):
    translate_fn, key_env = TRANSLATE_FN.get(provider, (None, None))
    if translate_fn is None:
        print(f"未知 provider: {provider}，支持: {list(TRANSLATE_FN)}")
        sys.exit(1)

    api_key = os.environ.get(key_env)
    if not api_key:
        print(f"未设置 {key_env}，跳过翻译")
        return 0

    # 从路径推断 locale
    locale = 'zh_Hans_CN'
    for part in Path(po_path).parts:
        if part in HUMAN_LANG_MAP:
            locale = part
            break

    print(f"文件: {po_path}")
    print(f"Locale: {locale}  Provider: {provider}  模型/端点: ", end='')
    if provider == 'openai':
        print(f"{os.environ.get('OPENAI_MODEL', DEFAULT_OPENAI_MODEL)} @ "
              f"{os.environ.get('OPENAI_API_URL', DEFAULT_OPENAI_URL)}")
    elif provider == 'anthropic':
        print(f"{os.environ.get('ANTHROPIC_MODEL', DEFAULT_ANTHROPIC_MODEL)} @ "
              f"{os.environ.get('ANTHROPIC_API_URL', DEFAULT_ANTHROPIC_URL)}")
    elif provider == 'deepl':
        print(os.environ.get('DEEPL_API_URL', DEFAULT_DEEPL_URL))

    entries = read_po_file(po_path)
    untranslated = [e for e in entries if not e['msgstr'] and e['msgid']]
    print(f"待翻译: {len(untranslated)}/{len(entries)} 条")

    translated_count = 0
    for i, entry in enumerate(untranslated):
        msgid = entry['msgid']
        try:
            result = translate_fn(msgid, api_key, locale)
            # 写回到 entries 对应位置
            for e in entries:
                if e['msgid'] == msgid and not e['msgstr']:
                    e['msgstr'] = result
                    break
            translated_count += 1
            print(f"  [{i+1}/{len(untranslated)}] ✓ {msgid[:40]!r} → {result[:30]!r}")
            time.sleep(0.3)  # 避免触发速率限制
        except Exception as exc:
            print(f"  [{i+1}/{len(untranslated)}] ✗ {msgid[:40]!r} — {exc}")

    if translated_count > 0:
        write_po_file(po_path, entries)
        print(f"\n✓ 翻译完成: {translated_count}/{len(untranslated)} 条已写入")
    else:
        print("没有新条目被翻译")

    return translated_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    po_path  = sys.argv[1]
    provider = 'deepl'
    if '--provider' in sys.argv:
        idx = sys.argv.index('--provider')
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]

    if not os.path.exists(po_path):
        print(f"错误: 文件不存在: {po_path}")
        sys.exit(1)

    auto_translate(po_path, provider)


if __name__ == '__main__':
    main()
