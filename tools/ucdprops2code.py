#!/usr/bin/env python3

# Generates code from unicode properties db


import sys
import itertools
import pathlib
import re
import pprint
import collections
import math

from typing import Any, Iterable

try:
    batched = itertools.batched
except AttributeError:
    # Copied from https://docs.python.org/3/library/itertools.html#itertools.batched
    def batched(iterable, n):
        # batched('ABCDEFG', 3) --> ABC DEF G
        if n < 1:
            raise ValueError("n must be at least one")
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, n)):
            yield batch


def is_one_value(vals):
    return len(vals) == 1 and isinstance(vals[0], int)


def is_one_range(vals):
    return len(vals) == 1 and not isinstance(vals[0], int)


def all_vals(vals):
    for row in vals:
        if isinstance(row, int):
            yield row
        else:
            yield from range(row[0], row[1] + 1)


def fmt(v: int) -> str:
    # format values the same as in the text source for easy grepping
    return f"{v:04X}"


def augiter(content: Iterable):
    "yields is_first, is_last, item from content"
    all_items = tuple(content)
    last_index = len(all_items) - 1
    for i, item in enumerate(all_items):
        is_first = i == 0
        is_last = i == last_index
        yield is_first, is_last, item


def bsearch(indent: int, items: list, n: int):
    # n is if tests at same level.  2 means binary search, 3 is trinary etc
    indent_ = "    " * indent

    if len(items) > n:
        # break into smaller
        step = math.ceil(len(items) / n)
        chunks = list(range(0, len(items), step))
        for is_first, is_last, begin in augiter(chunks):
            test = None
            if not is_last:
                test = items[chunks[1 + chunks.index(begin)]][0]
            if is_first:
                yield f"{ indent_ }if c < 0x{ test:04X}:"
            elif is_last:
                yield f"{ indent_ }else:"
            else:
                yield f"{ indent_ }elif c < 0x{ test:04X}:"
            yield from bsearch(indent + 1, items[begin : begin + step], n)
    else:
        for is_first, is_last, (start, end, cat) in augiter(items):
            if start == end:
                test = f"c == 0x{ start:04X}"
            else:
                test = f"0x{ start:04X} <= c <= 0x{ end:04X}"
            if not is_last:
                yield f"{ indent_ }if { test }:"
                yield f"{ indent_ }    return GC.{ cat }"
            else:
                yield f"{ indent_ }# { test }"
                yield f"{ indent_ }return GC.{ cat }"


# We do Python code for testing and development
def generate_python() -> str:
    out: list[str] = []
    out.append("import enum")
    out.append("")
    out.append(f'unicode_version = "{ ucd_version }"')
    out.append("")
    out.append("")

    # grapheme only for the moment
    out.append(f"# Grapheme categories")
    out.append("class GC(enum.Enum):")
    for i, cat in enumerate(sorted(set(v[2] for v in grapheme_ranges))):
        out.append(f"    { cat } = { i }")
    out.append("")
    out.append("")
    out.append("def grapheme_category(c: int) -> GC:")
    out.append('    "Returns category corresponding to codepoint"')
    out.append("")

    # ::TODO:: generate a direct lookup table for first N codepoints
    # where N is likely 256 so they don't need to go through bsearch

    out.extend(bsearch(1, grapheme_ranges, 2))

    return "\n".join(out) + "\n"


props = {
    "grapheme": {},
    "word": {},
    "sentence": {},
}

ucd_version = None


def extract_version(filename: str, source: str):
    global ucd_version
    if filename == "emoji-data.txt":
        for line in source.splitlines():
            if line.startswith("# Used with Emoji Version "):
                mo = re.match(r".*Version (?P<version>[^\s]+)\s.*", line)
                break
        else:
            raise ValueError("No matching version line found")
    else:
        mo = re.match(r"# [^-]+-(?P<version>.*)\.txt", source.splitlines()[0])
    # we only care about major.minor
    version = ".".join(mo.group("version").split(".")[:2])
    if ucd_version is None:
        ucd_version = version
    elif ucd_version != version:
        sys.exit(f"Already saw {ucd_version=} but {filename=} is {version=}")


def parse_source_lines(source: str):
    for line in source.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        line = line[: line.index("#")]
        vals, prop = line.split(";", 1)
        prop = prop.strip()
        vals = vals.strip().split("..")
        if len(vals) == 1:
            yield int(vals[0], 16), None, prop
        else:
            yield int(vals[0], 16), int(vals[1], 16), prop


def populate(source: str, dest: dict[str, Any]):
    for start, end, prop in parse_source_lines(source):
        try:
            accumulate = dest[prop]
        except KeyError:
            accumulate = dest[prop] = []

        if end is None:
            accumulate.append(start)
        else:
            accumulate.append((start, end))


def extract_prop(source: str, dest: dict[str, Any], prop_name: str, name: str | None = None):
    if name is None:
        name = prop_name
    assert name not in dest
    accumulate = dest[name] = []

    for start, end, prop in parse_source_lines(source):
        if prop == prop_name:
            if end is None:
                accumulate.append(start)
            else:
                accumulate.append((start, end))

    assert len(accumulate) > 0


def read_props(data_dir: str):
    if data_dir:
        url = pathlib.Path(data_dir) / "emoji-data.txt"
    else:
        url = "https://www.unicode.org/Public/UCD/latest/ucd/emoji/emoji-data.txt"

    print("Reading", url)
    if isinstance(url, str):
        source = urllib.request.urlopen(url).read().decode("utf8")
    else:
        source = url.read_text("utf8")

    extract_version("emoji-data.txt", source)
    extract_prop(source, props["grapheme"], "Extended_Pictographic")

    if data_dir:
        url = pathlib.Path(data_dir) / "DerivedCoreProperties.txt"
    else:
        url = "https://www.unicode.org/Public/UCD/latest/ucd/DerivedCoreProperties.txt"

    print("Reading", url)
    if isinstance(url, str):
        source = urllib.request.urlopen(url).read().decode("utf8")
    else:
        source = url.read_text("utf8")

    extract_version("DerivedCoreProperties.txt", source)
    extract_prop(source, props["grapheme"], "InCB; Linker", "InCB_Linker")
    extract_prop(source, props["grapheme"], "InCB; Consonant", "InCB_Consonant")
    extract_prop(source, props["grapheme"], "InCB; Extend", "InCB_Extend")

    for top in "Grapheme", "Word", "Sentence":
        if data_dir:
            url = pathlib.Path(data_dir) / f"{ top }BreakProperty.txt"
        else:
            url = f"https://www.unicode.org/Public/UCD/latest/ucd/auxiliary/{ top }BreakProperty.txt"
        print("Reading", url)
        if isinstance(url, str):
            source = urllib.request.urlopen(url).read().decode("utf8")
        else:
            source = url.read_text("utf8")
        extract_version(f"{ top }BreakProperty.txt", source)
        populate(source, props[top.lower()])


grapheme_ranges = []


def generate_grapheme_ranges():
    all_cp = {}
    # somewhat messy because eg Extend and InCB_Extend overlap
    # so we turn into a set in that case
    for category, vals in props["grapheme"].items():
        for val in all_vals(vals):
            if val in all_cp:
                existing = all_cp[val]
                # sets aren't hashable so we keep things as a sorted
                # tuple, and do this dance to update them
                cat = tuple(sorted((set(existing) if isinstance(existing, tuple) else {existing}) | {category}))
            else:
                cat = category
            all_cp[val] = cat

    print("Categories and members")
    by_cat = collections.Counter()
    for v in all_cp.values():
        by_cat[v] += 1
    pprint.pprint(by_cat)

    last = None

    adjust = {
        # only one codepoint
        ("InCB_Extend", "ZWJ"): "ZWJ",
        # same semantics as ZWJ if followed by InCB_Consonant
        ("Extend", "InCB_Linker"): "InCB_Linker",
        # all InCB_Extend are also marked as Extend, but not all extend are InCB_Extend
        ("Extend", "InCB_Extend"): "InCB_Extend",
    }

    for cp in range(0, sys.maxunicode + 1):
        cat = all_cp.get(cp, "Other")
        cat = adjust.get(cat, cat)
        assert isinstance(cat, str), f"{cat=} is not a str"
        if cat != last:
            grapheme_ranges.append([cp, cp, cat])
        else:
            grapheme_ranges[-1][1] = cp
        last = cat


py_code_header = f"""\
# Generated by { sys.argv[0] } - Do not edit

"""

if __name__ == "__main__":
    import argparse
    import urllib.request

    p = argparse.ArgumentParser(description="Generate code from Unicode properties")
    p.add_argument(
        "--data-dir",
        help="Directory containing local copies of the relevant unicode database files.  If "
        "not supplied the latest files are read from https://www.unicode.org/Public/UCD/latest/ucd/",
    )
    p.add_argument("out_py", type=argparse.FileType("w", encoding="utf8"), help="File to write python code to")

    options = p.parse_args()

    read_props(options.data_dir)

    generate_grapheme_ranges()

    py_code = generate_python()
    options.out_py.write(py_code_header)
    options.out_py.write(py_code)
    options.out_py.close()
