#!/usr/bin/env python3

"""
An implementation of Unicode Text Segmentation
primarily intended for text search

https://www.unicode.org/reports/tr29/
"""


from __future__ import annotations

# This module is expected to be C in the future, so pretend these methods
# are present in this module
from _tr29db import *


def grapheme_next_length(text: str, offset: int = 0) -> int:
    """Returns how long a User Perceived Character is

    For example regional indicators are in pairs, and a base codepoint
    can be combined with zero or more additional codepoints providing
    diacritics, marks, and variations.

    :param text: The text to examine
    :param offset: The first codepoint to examine

    :returns:  How many codepoints make up one user perceived
      character.  You should extract ``text[offset:offset+len]``

    """
    lt = len(text)
    if offset < 0 or offset > lt:
        raise ValueError(f"{offset=} is out of bounds 0 - { lt }")

    # At end?
    if offset == lt:
        return 0

    # Only one char?
    if offset + 1 == lt:
        return 1

    # rules are based on lookahead so we use pos to indicate where we are looking
    char = ord(text[offset])
    lookahead = ord(text[offset + 1])

    # GB3
    if is_grapheme_CR(char) and is_grapheme_LF(lookahead):
        return 2

    # GB4/5
    if is_grapheme_Control(char) or is_grapheme_CR(char) or is_grapheme_LF(char):
        return 1

    # State machine for the rest
    pos = offset
    while pos < lt:
        # Do lookahead
        char = ord(text[pos])
        pos += 1
        try:
            lookahead = ord(text[pos])
        except IndexError:
            return pos - offset

        # GB9B
        if is_grapheme_Prepend(char):
            continue

        # GB9a/11
        if is_grapheme_ZWJ(lookahead) or is_grapheme_Extend(lookahead) or is_grapheme_SpacingMark(lookahead):
            pos += 1
            continue

        # GB12/13
        if is_grapheme_Regional_Indicator(char) and is_grapheme_Regional_Indicator(lookahead):
            # suck up the pair then repeat GB9/11
            pos += 1
            try:
                lookahead = ord(text[pos])
            except IndexError:
                return pos - offset
            if not (
                is_grapheme_ZWJ(lookahead)
                or is_grapheme_Extend(lookahead)
                or is_grapheme_Prepend(lookahead)
                or is_grapheme_SpacingMark(lookahead)
            ):
                return pos - offset
            continue

        # GB6
        if is_grapheme_L(char) and (
            is_grapheme_L(lookahead)
            or is_grapheme_V(lookahead)
            or is_grapheme_LV(lookahead)
            or is_grapheme_LVT(lookahead)
        ):
            continue

        # GB7
        if (is_grapheme_LV(char) or is_grapheme_V(char)) and (is_grapheme_V(lookahead) or is_grapheme_T(lookahead)):
            continue

        # GB8
        if (is_grapheme_LVT(char) or is_grapheme_T(char)) and is_grapheme_T(lookahead):
            continue

        # GB999
        return pos - offset

    return pos - offset


if __name__ == "__main__":
    import argparse
    import unicodedata
    import os
    import textwrap
    import sys
    import apsw.fts
    import apsw.ext

    width = 80
    if sys.stdout.isatty():
        width = os.get_terminal_size(sys.stdout.fileno()).columns

    parser = argparse.ArgumentParser()
    parser.set_defaults(function=None)
    subparsers = parser.add_subparsers()
    p = subparsers.add_parser("breaktest", help="Run Unicode test file")
    p.set_defaults(function="breaktest")
    p.add_argument("test", choices=("grapheme", "word", "sentence"), help="What to test")
    p.add_argument("file", help="break test text file.  They can be downloaded from https://www.unicode.org/Public/UCD/latest/ucd/auxiliary/", type=argparse.FileType("rt", encoding="utf8"))

    p = subparsers.add_parser("show", help="Run against provided text")
    p.set_defaults(function="show")

    p.add_argument(
        "--show", default="grapheme", choices=("grapheme", "word", "sentence"), help="What to show [%(default)s]"
    )
    p.add_argument("--text-file", type=argparse.FileType("rt", encoding="utf8"))
    p.add_argument("--width", default=width, help="Output width [%(default)s]", type=int)
    p.add_argument("text", nargs="*", help="Text to segment unless --text-file used")

    options = parser.parse_args()

    if not options.function:
        p.error("You must specify a sub-command")

    if options.function == "show":
        if not options.text_file and not options.text:
            p.error("You must specify at least --text-file or text arguments")

        text = ""
        if options.text:
            text += " ".join(options.text)
        if options.text_file:
            if text:
                text += " "
            text += options.text_file.read()

        len_func = globals()[f"{ options.show }_next_length"]
        flags_func = globals()[f"all_{ options.show }_flags"]

        counter = 0
        offset = 0
        while offset < len(text):
            ncp = len_func(text, offset)
            print(f"#{ counter } offset { offset } codepoints { ncp }")
            codepoints = []
            names_flags = []
            for i in range(offset, offset + ncp):
                c = text[i]
                codepoints.append("%04X" % ord(c))
                try:
                    name = unicodedata.name(c)
                except ValueError:
                    name = codepoints[-1]
                cat = unicodedata.category(c)
                name += f" ({ cat } { apsw.fts.unicode_categories[cat] })"
                flags = ",".join(flags_func(ord(c)))
                if flags:
                    flags = f" : { flags }"
                names_flags.append("{" + f"{name}{ flags }" + "}")
            print("\n".join(textwrap.wrap(" ".join(codepoints), width=options.width)))
            print("\n".join(textwrap.wrap(" ".join(names_flags), width=options.width)))
            offset += ncp

    else:
        assert options.function == "breaktest"
        len_func = globals()[f"{ options.test }_next_length"]
        ok = "÷"
        not_ok = "×"
        fails : list[str] = []
        for line_num, line in enumerate(options.file, 1):
            if not line.strip() or line.startswith("#"):
                continue
            line = line.split("#")[0].strip().split()
            assert line[0] == ok, f"Line { line_num } doesn't start with { ok }!"
            assert line[-1] == ok, f"Line { line_num } doesn't end with { ok }!"
            line = line[1:]
            text = ""
            breaks = []
            while line:
                c = line.pop(0)
                if c == not_ok:
                    continue
                if c == ok:
                    breaks.append(len(text))
                    continue
                text += chr(int(c, 16))

            offset = 0
            seen : list[int]= []
            lf = len(fails)
            while offset < len(text):
                try:
                  length = len_func(text, offset)
                except:
                    apsw.ext.print_augmented_traceback(*sys.exc_info())
                    raise
                break_pos = offset + length
                if break_pos not in breaks:
                    fails.append(f"Line { line_num } got unexpected break at { break_pos } - expected are { breaks }")
                    break
                seen.append(break_pos)
                offset = break_pos
            if len(fails) != lf:
                continue
            if set(seen) != set(breaks):
                fails.append(f"Line { line_num } got breaks at { seen } expected at { breaks }")

        if fails:
            print("Tests failed:", file=sys.stderr)
            for fail in fails:
                print(fail, file=sys.stderr)
            sys.exit(2)
