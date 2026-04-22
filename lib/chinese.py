"""
Chinese name to pinyin conversion and variant generation.
"""

try:
    from pypinyin import lazy_pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False
    import re

# Fallback simple pinyin mapping for common Chinese surnames
SURNAME_MAP = {
    '张': 'zhang', '李': 'li', '王': 'wang', '刘': 'liu', '陈': 'chen',
    '杨': 'yang', '黄': 'huang', '赵': 'zhao', '周': 'zhou', '吴': 'wu',
    '徐': 'xu', '孙': 'sun', '马': 'ma', '朱': 'zhu', '胡': 'hu',
    '郭': 'guo', '何': 'he', '林': 'lin', '罗': 'luo', '高': 'gao',
    '梁': 'liang', '郑': 'zheng', '宋': 'song', '谢': 'xie', '唐': 'tang',
    '韩': 'han', '曹': 'cao', '许': 'xu', '邓': 'deng', '冯': 'feng',
    '程': 'cheng', '曹': 'cao', '彭': 'peng', '潘': 'pan', '汪': 'wang',
    '田': 'tian', '董': 'dong', '袁': 'yuan', '于': 'yu', '余': 'yu',
    '苏': 'su', '卢': 'lu', '蒋': 'jiang', '蔡': 'cai', '贾': 'jia',
    '丁': 'ding', '魏': 'wei', '薛': 'xue', '叶': 'ye', '阎': 'yan',
    '余': 'yu', '潘': 'pan', '杜': 'du', '夏': 'xia', '钟': 'zhong',
    '汪': 'wang', '田': 'tian', '任': 'ren', '姜': 'jiang', '范': 'fan',
    '方': 'fang', '石': 'shi', '姚': 'yao', '谭': 'tan', '廖': 'liao',
    '邹': 'zhou', '熊': 'xiong', '金': 'jin', '陆': 'lu', '郝': 'hao',
    '孔': 'kong', '白': 'bai', '崔': 'cui', '康': 'kang', '毛': 'mao',
    '邱': 'qiu', '秦': 'qin', '江': 'jiang', '史': 'shi', '顾': 'gu',
    '侯': 'hou', '邵': 'shao', '孟': 'meng', '龙': 'long', '万': 'wan',
    '段': 'duan', '漕': 'cao', '钱': 'qian', '汤': 'tang', '尹': 'yin',
    '黎': 'li', '易': 'yi', '常': 'chang', '武': 'wu', '乔': 'qiao',
    '贺': 'he', '赖': 'lai', '龚': 'gong', '文': 'wen'
}

# Common Chinese given names and their pinyin
COMMON_GIVEN_NAMES = {
    '伟': 'wei', '芳': 'fang', '娜': 'na', '秀英': 'xiuying', '敏': 'min',
    '静': 'jing', '丽': 'li', '强': 'qiang', '磊': 'lei', '军': 'jun',
    '洋': 'yang', '勇': 'yong', '艳': 'yan', '杰': 'jie', '涛': 'tao',
    '明': 'ming', '超': 'chao', '秀兰': 'xiulan', '霞': 'xia', '平': 'ping',
    '刚': 'gang', '桂英': 'guiying', '华': 'hua', '红': 'hong', '玉兰': 'yulan',
    '志强': 'zhiqiang', '英': 'ying', '文': 'wen', '芳': 'fang', '敏': 'min',
    '丽': 'li', '强': 'qiang', '涛': 'tao', '杰': 'jie', '超': 'chao'
}


def chinese_to_pinyin(name: str) -> dict:
    """
    Convert Chinese name to pinyin variants.

    Returns dict with keys:
    - full: zhangsan
    - dotted: zhang.san
    - reversed: san.zhang (family.given)
    - initial: zs (first letter of each)
    - family_first: zhangsan (same as full)
    """
    if not PYPINYIN_AVAILABLE:
        return _simple_chinese_convert(name)

    # Split name into characters
    chars = list(name)

    # Get pinyin for each character
    pinyin_list = lazy_pinyin(chars, style=Style.NORMAL)

    # Separate surname and given name
    if len(chars) >= 2:
        surname_pinyin = pinyin_list[0]
        given_pinyin = ''.join(pinyin_list[1:])
        given_pinyins = pinyin_list[1:]
    else:
        surname_pinyin = pinyin_list[0]
        given_pinyin = ''
        given_pinyins = []

    return {
        'full': f"{surname_pinyin}{given_pinyin}",
        'full_dotted': f"{surname_pinyin}.{given_pinyin}",
        'reversed': f"{given_pinyin}.{surname_pinyin}",
        'reversed_no_dot': f"{given_pinyin}{surname_pinyin}",
        'initial': f"{surname_pinyin[0]}{given_pinyin[0] if given_pinyin else ''}",
        'surname': surname_pinyin,
        'given': given_pinyin,
        'surname_initial': surname_pinyin[0],
        'given_list': given_pinyins,
        'all_pinyin': pinyin_list
    }


def _simple_chinese_convert(name: str) -> dict:
    """Fallback conversion without pypinyin."""
    result = {'all_pinyin': [], 'surname': '', 'given': ''}

    for char in name:
        if char in SURNAME_MAP:
            pinyin = SURNAME_MAP[char]
        else:
            # Try to match multi-char given names
            pinyin = char
        result['all_pinyin'].append(pinyin)

    if len(result['all_pinyin']) >= 2:
        result['surname'] = result['all_pinyin'][0]
        result['given'] = ''.join(result['all_pinyin'][1:])
    else:
        result['surname'] = ''.join(result['all_pinyin'])
        result['given'] = ''

    result['full'] = f"{result['surname']}{result['given']}"
    result['full_dotted'] = f"{result['surname']}.{result['given']}"
    result['reversed'] = f"{result['given']}.{result['surname']}"
    result['reversed_no_dot'] = f"{result['given']}{result['surname']}"
    result['initial'] = f"{result['surname'][0] if result['surname'] else ''}{result['given'][0] if result['given'] else ''}"
    result['surname_initial'] = result['surname'][0] if result['surname'] else ''
    result['given_list'] = result['all_pinyin'][1:]

    return result


def generate_pinyin_formats(pinyin_data: dict) -> list[str]:
    """Generate all possible pinyin format strings."""
    formats = []

    surname = pinyin_data['surname']
    given = pinyin_data['given']
    given_first = given[0] if given else ''
    full = pinyin_data['full']
    initial = pinyin_data['initial']
    reversed_name = pinyin_data['reversed']

    # Basic formats
    formats.append(full)  # zhangsan
    formats.append(f"{surname}.{given}")  # zhang.san
    formats.append(f"{surname}_{given}")  # zhang_san
    formats.append(f"{surname}-{given}")  # zhang-san
    formats.append(reversed_name)  # san.zhang
    formats.append(pinyin_data['reversed_no_dot'])  # sanzhang
    formats.append(f"{surname[0]}{given}")  # zsan
    formats.append(f"{surname[0]}.{given}")  # z.san
    formats.append(f"{given_first}{surname}")  # szhang
    formats.append(f"{given_first}.{surname}")  # s.zhang

    # With duplicate suffixes
    for suffix in ['01', '02', '03', '1', '2', '3', 'a', 'b']:
        formats.append(f"{full}{suffix}")
        formats.append(f"{surname}.{given}{suffix}")

    # With year suffixes
    for year in ['90', '95', '00', '85']:
        formats.append(f"{full}{year}")
        formats.append(f"{full}19{year}")

    return list(set(formats))  # Remove duplicates


def is_chinese_name(name: str) -> bool:
    """Check if name contains Chinese characters."""
    if not PYPINYIN_AVAILABLE:
        return any('一' <= char <= '鿿' for char in name)
    else:
        return any('一' <= char <= '鿿' for char in name)


def parse_name(name: str) -> dict:
    """
    Parse a name string into structured components.

    Handles:
    - Chinese: 张伟
    - English: David Zhang
    - Pinyin: zhangwei
    - Mixed: 张伟 (David)
    """
    result = {
        'original': name,
        'is_chinese': is_chinese_name(name),
        'chinese_name': None,
        'english_first': None,
        'english_last': None,
        'pinyin': None
    }

    if result['is_chinese']:
        # Parse Chinese name
        result['chinese_name'] = name
        result['pinyin'] = chinese_to_pinyin(name)

        # Check if English name also provided (in parentheses)
        import re
        english_match = re.search(r'[A-Za-z]+', name)
        if english_match:
            # Might have English name embedded
            pass
    else:
        # English name - parse as "First Last"
        parts = name.strip().split()
        if len(parts) >= 2:
            result['english_first'] = parts[0].lower()
            result['english_last'] = parts[-1].lower()

    return result


def add_duplicate_suffix(base_email: str, suffix: str) -> str:
    """Add duplicate handling suffix to email."""
    local_part = base_email.split('@')[0]
    # Remove any existing numeric suffix
    local_part = ''.join([c for c in local_part if not c.isdigit()])
    return f"{local_part}{suffix}@{base_email.split('@')[1]}"