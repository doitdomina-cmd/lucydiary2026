"""파일(HWP/HWPX/TXT)에서 텍스트를 뽑고, 회차 구분 형식에 따라 회차별 글자수를 센다."""
import re
import struct
import zlib
import zipfile
import xml.etree.ElementTree as ET

# 드롭다운에 보이는 이름 -> 한 줄 전체가 이 모양이면 회차 시작으로 본다. (\d+)가 회차 번호.
MARKERS = {
    "1.": r"(\d+)\.",
    "@1.": r"@\s*(\d+)\.",
    "1화": r"(\d+)\s*화",
    "<1화>": r"<\s*(\d+)\s*화\s*>",
    "<1>": r"<\s*(\d+)\s*>",
    "제1화": r"제\s*(\d+)\s*화",
    "1)": r"(\d+)\)",
    "#1": r"#\s*(\d+)",
}


# ---------- 텍스트 추출 ----------
def _hwp_para_text(data: bytes) -> str:
    out = []
    i, n = 0, len(data)
    while i + 1 < n:
        c = struct.unpack_from("<H", data, i)[0]
        if c in (0, 13) or 24 <= c <= 31:
            i += 2
        elif c == 10:
            out.append("\n")
            i += 2
        elif c < 32:  # 확장/인라인 컨트롤: 총 16바이트
            i += 16
        else:
            out.append(chr(c))
            i += 2
    return "".join(out)


def read_hwp(path: str) -> str:
    import olefile

    ole = olefile.OleFileIO(path)
    try:
        header = ole.openstream("FileHeader").read()
        flags = struct.unpack_from("<I", header, 36)[0]
        if flags & 0x02:
            raise ValueError("암호가 걸린 HWP는 읽을 수 없어요.")
        compressed = bool(flags & 0x01)
        sections = sorted(
            (e for e in ole.listdir() if len(e) == 2 and e[0] == "BodyText" and e[1].startswith("Section")),
            key=lambda e: int(re.sub(r"\D", "", e[1]) or 0),
        )
        paras = []
        for e in sections:
            raw = ole.openstream(e).read()
            if compressed:
                raw = zlib.decompress(raw, -15)
            paras.extend(_hwp_records(raw))
        return "\n".join(paras)
    finally:
        ole.close()


def _hwp_records(raw: bytes):
    paras, i, n = [], 0, len(raw)
    cur = None
    while i + 4 <= n:
        h = struct.unpack_from("<I", raw, i)[0]
        tag, size = h & 0x3FF, (h >> 20) & 0xFFF
        i += 4
        if size == 0xFFF:
            size = struct.unpack_from("<I", raw, i)[0]
            i += 4
        body = raw[i:i + size]
        i += size
        if tag == 0x42:  # PARA_HEADER: 새 문단
            if cur is not None:
                paras.append(cur)
            cur = ""
        elif tag == 0x43:  # PARA_TEXT
            cur = (cur or "") + _hwp_para_text(body)
    if cur is not None:
        paras.append(cur)
    return paras


def read_hwpx(path: str) -> str:
    paras = []
    with zipfile.ZipFile(path) as z:
        names = sorted(
            (m for m in z.namelist() if re.match(r"Contents/section\d+\.xml$", m)),
            key=lambda m: int(re.search(r"(\d+)\.xml$", m).group(1)),
        )
        for m in names:
            root = ET.fromstring(z.read(m))
            for p in root.iter():
                if p.tag.endswith("}p"):
                    s = "".join(t.text or "" for t in p.iter() if t.tag.endswith("}t"))
                    paras.append(s)
    return "\n".join(paras)


def read_txt(path: str) -> str:
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp949", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeError:
            continue
    return raw.decode("utf-8", "ignore")


def read_text(path: str) -> str:
    low = path.lower()
    if low.endswith(".hwp"):
        return read_hwp(path)
    if low.endswith(".hwpx"):
        return read_hwpx(path)
    return read_txt(path)


# ---------- 회차 나누기 / 글자수 ----------
def split_episodes(text: str, marker_name: str):
    """[(회차번호 문자열, [본문 줄들]), ...] 구분 줄 앞의 내용은 버린다."""
    pat = re.compile(r"^[\s​﻿]*" + MARKERS[marker_name] + r"[\s​﻿]*$")
    eps, cur = [], None
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = pat.match(line)
        if m:
            cur = (m.group(1), [])
            eps.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return eps


def count_chars(lines, include_spaces=True) -> int:
    s = "".join(lines)
    if not include_spaces:
        s = re.sub(r"\s", "", s)
    else:
        s = s.replace("\t", "")
    return len(s)


def analyze(path: str, marker_name: str, include_spaces=True):
    text = read_text(path)
    return [(num, count_chars(lines, include_spaces)) for num, lines in split_episodes(text, marker_name)]
