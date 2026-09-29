"""小店记账工具的两个解析/计算函数。"""


class InputError(Exception):
    """用户输入非法。"""


def parse_qty(raw: str) -> int:
    """把命令行输入的数量解析为正整数；非法输入抛 InputError。"""
    if not raw.isdigit():
        raise InputError(f"数量必须是正整数: {raw}")
    qty = int(raw)
    if qty <= 0:
        raise InputError(f"数量必须是正整数: {raw}")
    return qty


def to_cents(yuan: float) -> int:
    """把元换算成分，四舍五入（0.5 进位）。"""
    return round(yuan * 100)


def half_up(x: float) -> int:
    """四舍五入到整数（0.5 进位）。"""
    return round(x)
