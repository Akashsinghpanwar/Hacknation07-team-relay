"""Extract text from the bundled PDF using its embedded ToUnicode maps."""

import pathlib
import re
import sys
import zlib


OBJECT = re.compile(rb"(\d+) 0 obj\s*(.*?)\s*endobj", re.S)
RANGE = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")
LITERAL = re.compile(rb"\((?:\\.|[^\\)])*\)", re.S)


def stream(obj):
    match = re.search(rb"stream\r?\n(.*?)\r?\nendstream", obj, re.S)
    if not match:
        return b""
    data = match.group(1)
    return zlib.decompress(data) if b"/FlateDecode" in obj[: match.start()] else data


def unescape(value):
    value = value[1:-1]
    result = bytearray()
    index = 0
    escapes = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
    while index < len(value):
        if value[index] != 92:
            result.append(value[index])
        elif index + 1 < len(value):
            index += 1
            if 48 <= value[index] <= 55:
                match = re.match(rb"[0-7]{1,3}", value[index:])
                result.append(int(match.group(), 8) % 256)
                index += len(match.group()) - 1
            elif value[index] in (10, 13):
                pass
            else:
                result.append(escapes.get(value[index], value[index]))
        index += 1
    return bytes(result)


def charmap(obj):
    mapping = {}
    for start, end, target in RANGE.findall(stream(obj)):
        start_n, end_n, target_n = int(start, 16), int(end, 16), int(target, 16)
        for code in range(start_n, end_n + 1):
            mapping[code] = chr(target_n + code - start_n)
    return mapping


def extract(pdf, selected_pages=None):
    objects = {int(match.group(1)): match.group(2) for match in OBJECT.finditer(pdf)}
    pages = [obj for obj in objects.values() if re.search(rb"/Type\s*/Page\b", obj)]
    for page_number, page in enumerate(pages, 1):
        if selected_pages and page_number not in selected_pages:
            continue
        content_id = int(re.search(rb"/Contents\s+(\d+)\s+0\s+R", page).group(1))
        resource_id = int(re.search(rb"/Resources\s+(\d+)\s+0\s+R", page).group(1))
        fonts = {}
        for name, font_id in re.findall(rb"/(TT\d+)\s+(\d+)\s+0\s+R", objects[resource_id]):
            font = objects[int(font_id)]
            cmap_ref = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", font)
            fonts[name] = charmap(objects[int(cmap_ref.group(1))]) if cmap_ref else {}
        print(f"\n{'=' * 20} PAGE {page_number} {'=' * 20}")
        for block in re.findall(rb"BT\s*(.*?)\s*ET", stream(objects[content_id]), re.S):
            font_match = re.search(rb"/(TT\d+)\s+[\d.]+\s+Tf", block)
            if not font_match:
                continue
            mapping = fonts.get(font_match.group(1), {})
            parts = []
            for operator in re.finditer(rb"(\[(?:.|\n)*?\]|\((?:\\.|[^\\)])*\))\s*T[Jj]", block):
                for literal in LITERAL.findall(operator.group(1)):
                    parts.append("".join(mapping.get(byte, "�") for byte in unescape(literal)))
            result = "".join(parts).strip()
            if result:
                print(result)


if __name__ == "__main__":
    extract(pathlib.Path(sys.argv[1]).read_bytes(), set(map(int, sys.argv[2:])) or None)
