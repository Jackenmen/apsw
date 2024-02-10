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


def grapheme_span(text: str, offset: int = 0) -> int:
    """Returns end of Grapheme /  User Perceived Character

    For example regional indicators are in pairs, and a base codepoint
    can be combined with zero or more additional codepoints providing
    diacritics, marks, and variations.

    :param text: The text to examine
    :param offset: The first codepoint to examine

    :returns:  Index of first codepoint not part of the grapheme
        starting at offset. You should extract ``text[offset:span]``

    """
    lt = len(text)
    if offset < 0 or offset > lt:
        raise ValueError(f"{offset=} is out of bounds 0 - { lt }")

    # GB1/2

    # At end?
    if offset == lt:
        return offset

    # Only one char?
    if offset + 1 == lt:
        return offset + 1

    # rules are based on lookahead so we use pos to indicate where we are looking
    pos = offset
    char = lookahead = grapheme_category(ord(text[pos]))

    def advance():
        nonlocal char, lookahead, pos, accepted
        if accepted is None:
            accepted = []
        else:
            accepted.append(char)
        char = lookahead
        pos += 1
        try:
            lookahead = grapheme_category(ord(text[pos]))
        except IndexError:
            # always break before Control so no need for separate end of file category
            lookahead = GC.Control
        # print(f"{offset=} {pos=} {char=} {lookahead=} {accepted=}")

    accepted = None

    while pos < lt:
        advance()

        # GB3
        if char is GC.CR and lookahead is GC.LF:
            return pos + 1

        # GB4
        if char is GC.Control or char is GC.CR or char is GC.LF:
            # break before if any chars are accepted
            if accepted:
                return pos - 1
            break

        # GB6
        if char is GC.L and (lookahead is GC.L or lookahead is GC.V or lookahead is GC.LV or lookahead is GC.LVT):
            continue

        # GB7
        if (char is GC.LV or char is GC.V) and (lookahead is GC.V or lookahead is GC.T):
            continue

        # GB8
        if (char is GC.LVT or char is GC.T) and lookahead is GC.T:
            continue

        # GB9 (InCB Extend and Linker chars are also marked extend)
        if lookahead is GC.Extend or lookahead is GC.InCB_Linker or lookahead is GC.InCB_Extend or lookahead is GC.ZWJ:
            continue

        # GB9a
        if lookahead is GC.SpacingMark:
            continue

        # GB9b
        if char is GC.Prepend:
            continue

        # GB9c
        if (
            lookahead is GC.InCB_Consonant
            and accepted
            and GC.InCB_Consonant in accepted
            and does_gb9c_apply(accepted + [char])
        ):
            continue

        # GB11
        if (
            lookahead is GC.Extended_Pictographic
            and char is GC.ZWJ
            and accepted
            and GC.Extended_Pictographic in accepted
            and does_gb11_apply(accepted)
        ):
            continue

        # GB12
        if char is GC.Regional_Indicator and lookahead is GC.Regional_Indicator:
            advance()
            # re-apply GB9
            if lookahead is GC.Extend or lookahead is GC.ZWJ or lookahead is GC.InCB_Extend:
                continue
            break

        # GB999
        break

    return pos


def does_gb9c_apply(seen: list[GC]) -> bool:
    bare_linker_seen = False
    for cp in reversed(seen):
        if cp is GC.InCB_Consonant:
            return bare_linker_seen
        if cp is GC.InCB_Linker:
            bare_linker_seen = True
            continue
        if cp is GC.InCB_Extend or cp is GC.ZWJ:
            continue
        return False
    assert False, "Can't reach here"


def does_gb11_apply(seen: list[GC]) -> bool:
    # we are sitting at ZWJ and looking back
    # should only see Extend (zero or more) then
    # extended_pictographic
    for cp in reversed(seen):
        if cp is GC.Extend or cp is GC.InCB_Extend:
            continue
        return cp is GC.Extended_Pictographic
    assert False, "Can't reach here"


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

    # ::TODO:: benchmark to work out best bsearch parameter

    parser = argparse.ArgumentParser()
    parser.set_defaults(function=None)
    subparsers = parser.add_subparsers()
    p = subparsers.add_parser("breaktest", help="Run Unicode test file")
    p.set_defaults(function="breaktest")
    # ::TODO:: a setting to show what pairs of codepoint kinds are not exercised by test text
    # eg (Extend, Prepend)
    p.add_argument("--fail-fast", default=False, action="store_true", help="Exit on first test failure")
    p.add_argument("test", choices=("grapheme", "word", "sentence"), help="What to test")
    # ::TODO:: auto download file if not provided
    p.add_argument(
        "file",
        help="break test text file.  They can be downloaded from https://www.unicode.org/Public/UCD/latest/ucd/auxiliary/",
        type=argparse.FileType("rt", encoding="utf8"),
    )

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

    def codepoint_details(c: str) -> str:
        try:
            name = unicodedata.name(c)
        except ValueError:
            name = "<NO NAME>"
        cat = unicodedata.category(c)
        name += f" ({ cat } { apsw.fts.unicode_categories[cat] })"
        flags = flags_func(ord(c)).name
        return "{U+" + ("%04X" % ord(c)) + f" {name} : { flags }" + "}"

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

        span_func = globals()[f"{ options.show }_span"]
        flags_func = globals()[f"{ options.show }_category"]

        counter = 0
        offset = 0
        while offset < len(text):
            span = span_func(text, offset)
            print(f"#{ counter } offset { offset } span { span } codepoints { span - offset }")
            codepoints = []
            for i in range(offset, span):
                codepoints.append(codepoint_details(text[i]))
            print("\n".join(textwrap.wrap(" ".join(codepoints), width=options.width)))
            offset = span

    else:
        assert options.function == "breaktest"
        span_func = globals()[f"{ options.test }_span"]
        flags_func = globals()[f"{ options.test }_category"]
        ok = "÷"
        not_ok = "\u00d7"
        fails: list[str] = []
        for line_num, line in enumerate(options.file, 1):
            orig_line = line
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

            def add_failinfo():
                fails.append(orig_line.strip())
                codepoints = []
                for c in text:
                    codepoints.append(codepoint_details(c))
                fails.append(" ".join(codepoints))
                fails.append("")

            offset = 0
            seen: list[int] = []
            lf = len(fails)
            while offset < len(text):
                try:
                    span = span_func(text, offset)
                except:
                    apsw.ext.print_augmented_traceback(*sys.exc_info())
                    raise
                if span not in breaks:
                    fails.append(
                        f"Line { line_num } got unexpected break at { span } - expected are { breaks }.  Seen { seen }"
                    )
                    add_failinfo()
                    break
                seen.append(span)
                offset = span
            if options.fail_fast and fails:
                break
            if len(fails) != lf:
                continue
            if set(seen) != set(breaks):
                fails.append(f"Line { line_num } got breaks at { seen } expected at { breaks }")
                add_failinfo()
            if options.fail_fast and fails:
                break

        if fails:
            print(f"{ len(fails)//4 } tests failed:", file=sys.stderr)
            for fail in fails:
                print(fail, file=sys.stderr)
            sys.exit(2)