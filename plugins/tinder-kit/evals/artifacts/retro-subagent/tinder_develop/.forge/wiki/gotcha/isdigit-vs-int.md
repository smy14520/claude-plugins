---
title: isdigit() 放行非十进制数字，int() 却拒收
tags: [bookkeeping, parsing]
---

# isdigit() 放行非十进制数字，int() 却拒收

## 现象

`str.isdigit()` 对 Unicode「数字类」字符返回 True（上标 `²`、`³` 等），但 `int()` 只接受十进制位。结果是预检形同虚设、转换处炸 `ValueError`：`parse_qty("²")` 曾因此绕过预检并在 `int("²")` 处裸抛（`tests/test_shop.py::test_parse_qty_rejects_superscript_digit`，修复见 commit 99ce1ed）。

## 复现

```bash
python3 -c 'print("²".isdigit()); int("²")'
```

## 守则

- 需要严格十进制输入时用 `isdecimal()` 做预检（与 `int()` 的接受范围一致），或用 `isascii() and isdigit()` 收紧到半角数字；不要依赖 `isdigit()`。
