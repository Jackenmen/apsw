# Process FTS5 queries as documented at https://www.sqlite.org/fts5.html#full_text_query_syntax

# The actual Lemon grammar used is at
# https://sqlite.org/src/file?name=ext/fts5/fts5parse.y

# Tokens https://sqlite.org/src/file?name=ext/fts5/fts5_expr.c
# fts5ExprGetToken

"""
There are 3 representations of a query available:

query string

   This the string syntax `accepted by FTS5
   <https://www.sqlite.org/fts5.html#full_text_query_syntax>`__ where
   you represent AND, OR, NEAR, column filtering etc inline in the
   string.  An example is::

     love AND (title:^"big world" NOT summary:"sunset cruise")

parsed

    This is a hierarchical representation using :mod:`dataclasses`
    with all fields present.  Represented as :class:`QUERY`, it uses
    :class:`PHRASE`, :class:`PHRASES`, :class:`NEAR`,
    :class:`COLUMNFILTER`, :class:`AND`, :class:`NOT`.  The string
    example truncated to a few lines omitting defaults is::

      AND(queries=[PHRASES(phrases=[PHRASE(phrase='love')]),
             NOT(match=COLUMNFILTER(columns=['title'],
                                    filter='include',
                                    query=PHRASES(phrases=[PHRASE(phrase='big '
                                                                         'world',
                                                                  initial=True,


dict

    This is a hierarchical representation using Python
    :class:`dictionaries <dict>` which is easy for logging, storing as
    JSON, and manipulating.  Fields containing default values are
    omitted.  When provided to methods in this module, you do not need
    to provide intermediate PHRASES and PHRASE and just Python lists
    and strings directly.  This is the easiest form to
    programmatically compose and modify queries in. The string example
    truncated to a few lines is::

      {'@': 'AND', 'queries': [
            "love",
            {'@': 'NOT',
              'match': {'@': 'COLUMNFILTER',
                        'columns': ['title'],
                        'filter': 'include',
                        'query': {'@': 'PHRASES',
                                  'phrases': [{'@': 'PHRASE',
                                               'initial': True,
                                               'phrase': 'big world'}]}},

    This form also allows omitting more of the structure like PHRASES in
    favour of a list of str.


.. list-table:: Conversion functions
    :header-rows: 1
    :widths: auto

    * - From type
      - To type
      - Conversion method
    * - query string
      - parsed
      - :func:`parse_query_string`
    * - parsed
      - dict
      - :func:`to_dict`
    * - dict
      - parsed
      - :func:`from_dict`
    * - parsed
      - query string
      - :func:`to_query_string`

Other helpful functionality includes:

* :func:`quote` to appropriately double quote strings
* :func:`extract_with_column_filters` to get a :class:`QUERY` for a node within
  an existing :class:`QUERY` but applying the intermediate column filters.
* :func:`applicable_columns` to work out which columns apply to part of a
  :class:`QUERY`
"""

from __future__ import annotations


import enum
import dataclasses

from typing import Any, Sequence, NoReturn, Literal, TypeAlias

# ::TODO:: figure out terminology  of docid versus rowid


class FTS5(enum.Enum):
    # these are assigned the same values as generated by
    # lemon, because why not.  fts5parse.h
    EOF = 0
    OR = 1
    AND = 2
    NOT = 3
    TERM = 4
    COLON = 5
    MINUS = 6
    LCP = 7
    RCP = 8
    STRING = 9
    LP = 10
    RP = 11
    CARET = 12
    COMMA = 13
    PLUS = 14
    STAR = 15
    # Add our own
    NEAR = 16


single_char_tokens = {
    "(": FTS5.LP,
    ")": FTS5.RP,
    "{": FTS5.LCP,
    "}": FTS5.RCP,
    ":": FTS5.COLON,
    ",": FTS5.COMMA,
    "+": FTS5.PLUS,
    "*": FTS5.STAR,
    "-": FTS5.MINUS,
    "^": FTS5.CARET,
}

# case sensitive
special_words = {
    "OR": FTS5.OR,
    "NOT": FTS5.NOT,
    "AND": FTS5.AND,
    "NEAR": FTS5.NEAR,
}


@dataclasses.dataclass
class Token:
    tok: FTS5
    pos: int
    value: str | None = None


def get_tokens(query: str) -> list[Token]:
    def skip_spacing():
        "Return True if we skipped any spaces"
        nonlocal pos
        original_pos = pos
        # fts5ExprIsspace
        while query[pos] in " \t\n\r":
            pos += 1
            if pos == len(query):
                return True

        return pos != original_pos

    def absorb_quoted():
        nonlocal pos
        if query[pos] != '"':
            return False

        # two quotes in a row keeps one and continues string
        start = pos + 1
        while True:
            pos = query.index('"', pos + 1)
            if query[pos : pos + 2] == '""':
                pos += 1
                continue
            break
        res.append(Token(FTS5.STRING, start, query[start:pos].replace('""', '"')))
        pos += 1
        return True

    def absorb_bareword():
        nonlocal pos
        start = pos

        while pos < len(query):
            # sqlite3Fts5IsBareword
            if (
                query[pos] in "0123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\x1a"
                or ord(query[pos]) >= 0x80
            ):
                pos += 1
            else:
                break
        if pos != start:
            s = query[start:pos]
            res.append(Token(special_words.get(s, FTS5.STRING), start, s))
            return True
        return False

    res: list[Token] = []
    pos = 0

    while pos < len(query):
        if skip_spacing():
            continue
        tok = single_char_tokens.get(query[pos])
        if tok is not None:
            res.append(Token(tok, pos))
            pos += 1
            continue

        if absorb_quoted():
            continue

        if absorb_bareword():
            continue

        raise ValueError(f"Invalid query character '{query[pos]}' in '{query}' at {pos=}")

    # add explicit EOF
    res.append(Token(FTS5.EOF, pos))

    # fts5 promotes STRING "NEAR" to token NEAR only if followed by "("
    # we demote to get the same effect
    for i in range(len(res) - 1):
        if res[i].tok == FTS5.NEAR and res[i + 1].tok != FTS5.LP:
            res[i].tok = FTS5.STRING

    return res


@dataclasses.dataclass
class PHRASE:
    "One `phrase <https://www.sqlite.org/fts5.html#fts5_phrases>`__"

    phrase: str
    "Text of the phrase"
    initial: bool = False
    "If True then the  phrase must match the beginning of a column"
    prefix: bool = False
    "If True then if it is a prefix search on the last token in phrase ('*' was used)"
    sequence: bool = False
    """If True then this phrase must follow tokens of previous phrase ('+' was used).
    initial and sequence can't both be True at the same time"""


@dataclasses.dataclass
class PHRASES:
    "Sequence of PHRASE"

    phrases: Sequence[PHRASE]


@dataclasses.dataclass
class NEAR:
    "`Near query <https://www.sqlite.org/fts5.html#fts5_near_queries>`__"

    phrases: PHRASES
    "Two or more phrases"
    distance: int = 10
    "Maximum distance between the phrases"


@dataclasses.dataclass
class COLUMNFILTER:
    """Limit query to `certain columns <https://www.sqlite.org/fts5.html#fts5_column_filters>`__

    This always reduces the columns that phrase matching will be done
    against.
    """

    columns: Sequence[str]
    "Limit phrase matching by these columns"
    filter: Literal["include"] | Literal["exclude"]
    "Including or excluding the columns"
    query: QUERY
    "query the filter applies to, including all nested queries"


@dataclasses.dataclass
class AND:
    "All queries `must match <https://www.sqlite.org/fts5.html#fts5_boolean_operators>`__"

    queries: Sequence[QUERY]


@dataclasses.dataclass
class OR:
    "Any query `must match <https://www.sqlite.org/fts5.html#fts5_boolean_operators>`__"

    queries: Sequence[QUERY]


@dataclasses.dataclass
class NOT:
    "match `must match <https://www.sqlite.org/fts5.html#fts5_boolean_operators>`__, but no_match `must not <https://www.sqlite.org/fts5.html#fts5_boolean_operators>`__"

    match: QUERY
    no_match: QUERY


# Sphinx makes this real ugly
# https://github.com/sphinx-doc/sphinx/issues/10541
QUERY: TypeAlias = COLUMNFILTER | NEAR | AND | OR | NOT | PHRASES
"""Type representing all query types."""


def to_dict(q: QUERY | PHRASE) -> dict[str, Any]:
    """Converts structure to a dict

    This is useful for pretty printing, logging, saving as JSON,
    modifying etc.

    The dict has a key `@` with value corresponding to the dataclass
    (eg `NEAR`, `PHRASE`, `AND`) and the same field names as the
    corresponding dataclasses.  Only fields with non-default values
    are emitted.
    """

    # @ was picked because it gets printed first if dict keys are sorted, and
    # won't conflict with any other key names

    if isinstance(q, PHRASES):
        return {"@": "PHRASES", "phrases": [to_dict(phrase) for phrase in q.phrases]}

    if isinstance(q, PHRASE):
        res = {"@": "PHRASE", "phrase": q.phrase}
        if q.prefix:
            res["prefix"] = True
        if q.sequence:
            res["sequence"] = True
        if q.initial:
            res["initial"] = True
        return res

    if isinstance(q, AND):
        return {"@": "AND", "queries": [to_dict(query) for query in q.queries]}

    if isinstance(q, OR):
        return {"@": "OR", "queries": [to_dict(query) for query in q.queries]}

    if isinstance(q, NOT):
        return {"@": "NOT", "match": to_dict(q.match), "no_match": to_dict(q.no_match)}

    if isinstance(q, NEAR):
        res = {"@": "NEAR", "phrases": to_dict(q.phrases)}
        if q.distance != 10:
            res["distance"] = q.distance
        return res

    if isinstance(q, COLUMNFILTER):
        return {"@": "COLUMNFILTER", "query": to_dict(q.query), "columns": q.columns, "filter": q.filter}

    raise ValueError(f"Unexpected value {q=}")


_dict_name_class = {
    "PHRASE": PHRASE,
    "PHRASES": PHRASES,
    "NEAR": NEAR,
    "COLUMNFILTER": COLUMNFILTER,
    "AND": AND,
    "OR": OR,
    "NOT": NOT,
}


def from_dict(d: dict[str, Any] | Sequence[str] | str) -> QUERY:
    """Turns dict back into a :class:`QUERY`

    You can take shortcuts putting `str` or `Sequence[str]` in
    places where PHRASES, or PHRASE are expected.  For example
    this is accepted::

        {
            "@": "AND,
            "queries": ["hello", "world"]
        }
    """
    if isinstance(d, (str, Sequence)):
        return _from_dict_as_phrases(d)

    _type_check(d, dict)

    if "@" not in d:
        raise ValueError(f"Expected key '@' in dict {d!r}")

    klass = _dict_name_class.get(d["@"])
    if klass is None:
        raise ValueError(f"\"{d['@']}\" is not a known query type")

    if klass is PHRASE or klass is PHRASES:
        return _from_dict_as_phrases(d)

    if klass is OR or klass is AND:
        queries = d.get("queries")

        if not isinstance(queries, Sequence) or len(queries) < 1:
            raise ValueError(f"{d!r} 'queries' must be sequence of at least 1 items")

        as_queries = [from_dict(query) for query in queries]
        if len(as_queries) == 1:
            return as_queries[0]

        return klass(as_queries)

    if klass is NEAR:
        phrases = d.get("phrases")

        as_phrases = _from_dict_as_phrases(phrases)
        if len(as_phrases.phrases) < 2:
            raise ValueError(f"NEAR requires at least 2 phrases in {phrases!r}")

        res = klass(as_phrases, _type_check(d.get("distance", 10), int))
        if res.distance < 1:
            raise ValueError(f"NEAR distance must be at least one in {d!r}")
        return res

    if klass is NOT:
        match, no_match = d.get("match"), d.get("no_match")
        if match is None or no_match is None:
            raise ValueError(f"{d!r} must have a 'match' and a 'no_match' key")

        return klass(from_dict(match), from_dict(no_match))

    assert klass is COLUMNFILTER

    columns = d.get("columns")

    if (
        columns is None
        or not isinstance(columns, Sequence)
        or len(columns) < 1
        or not all(isinstance(column, str) for column in columns)
    ):
        raise ValueError(f"{d!r} must have 'columns' key with at least one member sequence, all of str")

    filter = d.get("filter")

    if filter != "include" and filter != "exclude":
        raise ValueError(f"{d!r} must have 'filter' key with value of 'include' or 'exclude'")

    query = d.get("query")
    if query is None:
        raise ValueError(f"{d!r} must have 'query' value")

    return klass(columns, filter, from_dict(query))


def _type_check(v: Any, t: Any) -> Any:
    if not isinstance(v, t):
        raise ValueError(f"Expected {v!r} to be type {t}")
    return v


def _from_dict_as_phrase(item: Any, first: bool) -> PHRASE:
    "Convert anything reasonable into a PHRASE"
    if isinstance(item, str):
        return PHRASE(item)
    if isinstance(item, dict):
        if item.get("@") != "PHRASE":
            raise ValueError(f"{item!r} needs to be a dict with '@': 'PHRASE'")
        phrase = item.get("phrase")
        if phrase is None:
            raise ValueError(f"{item!r} must have phrase member")
        p = PHRASE(
            _type_check(phrase, str),
            _type_check(item.get("initial", False), bool),
            _type_check(item.get("prefix", False), bool),
            _type_check(item.get("sequence", False), bool),
        )
        if p.sequence and first:
            raise ValueError(f"First phrase {item!r} can't have sequence==True")
        if p.sequence and p.initial:
            raise ValueError(f"Can't have both sequence (+) and initial (^) set on same item {item!r}")
        return p
    raise ValueError(f"Can't convert { item!r} to a phrase")


def _from_dict_as_phrases(item: Any) -> PHRASES:
    "Convert anything reasonable into PHRASES"
    if isinstance(item, str):
        return PHRASES([PHRASE(item)])

    if isinstance(item, Sequence):
        phrases: list[PHRASE] = []
        for member in item:
            phrases.append(_from_dict_as_phrase(member, len(phrases) == 0))
        if len(phrases) == 0:
            raise ValueError(f"No phrase found in { member!r}")
        return PHRASES(phrases)

    if not isinstance(item, dict):
        raise ValueError(f"Can't turn {item!r} into phrases")

    kind = item.get("@")
    if kind not in {"PHRASE", "PHRASES"}:
        raise ValueError(f"Expected {item!r} '@' key with value of PHRASE or PHRASES")

    if kind == "PHRASE":
        return PHRASES([_from_dict_as_phrase(item, True)])

    phrases = item.get("phrases")
    if phrases is None or not isinstance(phrases, Sequence):
        raise ValueError(f"Expected 'phrases' value to be a sequence of {item!r}")

    return PHRASES([_from_dict_as_phrase(phrase, i == 0) for i, phrase in enumerate(phrases)])


# parentheses are not needed if the contained item has a lower
# priority than the container
_to_query_string_priority = {
    OR: 10,
    AND: 20,
    NOT: 30,
    # these are really all the same
    COLUMNFILTER: 50,
    NEAR: 60,
    PHRASES: 70,
    PHRASE: 80,
}


def _to_query_string_needs_parens(node: QUERY | PHRASE, child: QUERY | PHRASE) -> bool:
    return _to_query_string_priority[type(child)] < _to_query_string_priority[type(node)]


def to_query_string(q: QUERY | PHRASE) -> str:
    """Returns the corresponding query in text format"""
    if isinstance(q, PHRASE):
        r = ""
        if q.initial:
            r += "^ "
        if q.sequence:
            r += "+ "
        r += quote(q.phrase)
        if q.prefix:
            r += " *"
        return r

    if isinstance(q, PHRASES):
        # They are implicitly high priority AND together
        return " ".join(to_query_string(phrase) for phrase in q.phrases)

    if isinstance(q, (AND, OR)):
        r = ""
        for i, query in enumerate(q.queries):
            if i:
                # technically NEAR AND NEAR can leave the AND out but
                # we make it explicit
                r += " AND " if isinstance(q, AND) else " OR "
            if _to_query_string_needs_parens(q, query):
                r += "("
            r += to_query_string(query)
            if _to_query_string_needs_parens(q, query):
                r += ")"

        return r

    if isinstance(q, NOT):
        r = ""

        if _to_query_string_needs_parens(q, q.match):
            r += "("
        r += to_query_string(q.match)
        if _to_query_string_needs_parens(q, q.match):
            r += ")"

        r += " NOT "

        if _to_query_string_needs_parens(q, q.no_match):
            r += "("
        r += to_query_string(q.no_match)
        if _to_query_string_needs_parens(q, q.no_match):
            r += ")"

        return r

    if isinstance(q, NEAR):
        r = "NEAR(" + to_query_string(q.phrases)
        if q.distance != 10:
            r += f", {q.distance}"
        r += ")"
        return r

    if isinstance(q, COLUMNFILTER):
        r = ""
        if q.filter == "exclude":
            r += "-"
        if len(q.columns) > 1:
            r += "{"
        for i, column in enumerate(q.columns):
            if i:
                r += " "
            r += quote(column)
        if len(q.columns) > 1:
            r += "}"
        r += ": "
        if isinstance(q.query, (PHRASES, NEAR)):
            r += to_query_string(q.query)
        else:
            r += "(" + to_query_string(q.query) + ")"
        return r

    raise ValueError(f"Unexpected query item {q!r}")


def parse_query_string(query: str) -> QUERY:
    "Returns the corresponding :class:`QUERY` for the query string"
    # ::TODO:: rename Parser and fix this
    return Parser(query).parsed


def quote(text: str) -> str:
    """Quotes text if necessary to keep as one unit

    eg `hello' -> `hello`, `one two` -> `"one two"`,
    `` -> `""`, `one"two` -> `"one""two"`
    """
    # technically this will also apply to None and empty lists etc
    if not text:
        return '""'
    if any(c not in "0123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" and ord(c) < 0x80 for c in text):
        return '"' + text.replace('"', '""') + '"'
    return text


def extract_with_column_filters(node: QUERY, start: QUERY) -> QUERY:
    """Return a new `QUERY` for a query rooted at `start` with child `node`,
    with intermediate :class:`COLUMNFILTER` in between applied.

    This is useful if you want to execute a node from a top level
    query ensuring the column filters apply.
    """
    # ::TODO:: implement
    raise NotImplementedError()


def applicable_columns(node: QUERY, start: QUERY, columns: Sequence[str]) -> set[str]:
    """Return which columns apply to `node`

    You should use :meth:`apsw.fts.FTS5Table.columns_indexed` to get
    the column list for a table.
    """
    # ::TODO:: implement
    raise NotImplementedError()


# ::TODO:: make module stuff private like Parse and Tokenize


class ParseError(Exception):
    def __init__(self, query: str, message: str, position: int):
        # ::TODO:: fix using caret in message as it makes printing error ugly
        # and update all the messages to be better
        self.query = query
        self.message = message
        self.position = position


class Parser:
    def __init__(self, query: str):
        self.query = query
        self.tokens = get_tokens(query)
        self.token_pos = -1

        # ::TODO:: check what happens when empty query provided
        parsed = self.parse_query()
        if self.lookahead.tok != FTS5.EOF:
            self.error("Unexpected", self.lookahead)

        self.parsed = parsed

    def error(self, message: str, token: Token | None) -> NoReturn:
        raise ParseError(self.query, message, token.pos if token else 0)

    def _lookahead(self) -> Token:
        return self.tokens[self.token_pos + 1]

    lookahead = property(_lookahead, doc="Lookahead at next token")

    def take_token(self) -> Token:
        self.token_pos += 1
        return self.tokens[self.token_pos]

    def parse_part(self) -> QUERY:
        if self.lookahead.tok in {FTS5.MINUS, FTS5.LCP} or (
            self.lookahead.tok == FTS5.STRING and self.tokens[self.token_pos + 2].tok == FTS5.COLON
        ):
            return self.parse_colspec()

        if self.lookahead.tok == FTS5.LP:
            token = self.take_token()
            query = self.parse_query()
            if self.lookahead.tok != FTS5.RP:
                if self.lookahead.tok == FTS5.EOF:
                    self.error("unclosed (", token)
                else:
                    self.error(f"Expected ) to close ( at position { token.pos}", self.lookahead)
            self.take_token()
            return query

        if self.lookahead.tok == FTS5.NEAR:
            nears: list[NEAR] = []
            # NEAR groups may also be connected by implicit AND
            # operators.  Implicit AND operators group more tightly
            # than all other operators, including NOT
            while self.lookahead.tok == FTS5.NEAR:
                nears.append(self.parse_near())

            if len(nears) == 1:
                return nears[0]

            # We make the AND explicit
            return AND(nears)

        return self.parse_phrases()

    infix_precedence = {
        FTS5.OR: 10,
        FTS5.AND: 20,
        FTS5.NOT: 30,
    }

    def parse_query(self, rbp: int = 0):
        res = self.parse_part()

        while rbp < self.infix_precedence.get(self.lookahead.tok, 0):
            token = self.take_token()
            res = self.infix(token.tok, res, self.parse_query(self.infix_precedence[token.tok]))

        return res

    def parse_phrase(self, first: bool) -> PHRASE:
        initial = False
        sequence = False
        if self.lookahead.tok == FTS5.CARET:
            initial = True
            self.take_token()
        if not first and not initial and self.lookahead.tok == FTS5.PLUS:
            sequence = True
            self.take_token()

        token = self.take_token()
        if token.tok != FTS5.STRING:
            self.error("Expected a search term", token)

        res = PHRASE(token.value, initial, False, sequence)

        if self.lookahead.tok == FTS5.STAR:
            self.take_token()
            res.prefix = True

        return res

    def parse_phrases(self) -> PHRASES:
        phrases: list[PHRASE] = []

        phrases.append(self.parse_phrase(True))

        while self.lookahead.tok in {FTS5.PLUS, FTS5.STRING, FTS5.CARET}:
            phrases.append(self.parse_phrase(False))

        return PHRASES(phrases)

    def parse_near(self):
        # swallow NEAR
        self.take_token()

        # open parentheses
        token = self.take_token()
        if token.tok != FTS5.LP:
            self.error("Expected '(", token)

        # phrases
        phrases = self.parse_phrases()

        if len(phrases.phrases) < 2:
            self.error("At least two phrases must be present for NEAR", self.lookahead)

        # , distance
        distance = 10  # default
        if self.lookahead.tok == FTS5.COMMA:
            # absorb comma
            self.take_token()
            # distance
            number = self.take_token()
            if number.tok != FTS5.STRING or not number.value.isdigit():
                self.error("Expected number", number)
            distance = int(number.value)

        # close parentheses
        if self.lookahead.tok != FTS5.RP:
            self.error("Expected )", self.lookahead)
        self.take_token()

        return NEAR(phrases, distance)

    def parse_colspec(self):
        include = True
        columns: list[str] = []

        if self.lookahead.tok == FTS5.MINUS:
            include = False
            self.take_token()

        # inside curlys?
        if self.lookahead.tok == FTS5.LCP:
            self.take_token()
            while self.lookahead.tok == FTS5.STRING:
                columns.append(self.take_token().value)
            if len(columns) == 0:
                self.error("Expected column name", self.lookahead)
            if self.lookahead.tok != FTS5.RCP:
                self.error("Expected }", self.lookahead)
            self.take_token()
        else:
            if self.lookahead.tok != FTS5.STRING:
                self.error("Expected column name", self.lookahead)
            columns.append(self.take_token().value)

        if self.lookahead.tok != FTS5.COLON:
            self.error("Expected :", self.lookahead)
        self.take_token()

        if self.lookahead.tok == FTS5.LP:
            query = self.parse_query()
        elif self.lookahead.tok == FTS5.NEAR:
            query = self.parse_part()
        else:
            query = self.parse_phrases()

        return COLUMNFILTER(columns, "include" if include else "exclude", query)

    def infix(self, op: FTS5, left: QUERY, right: QUERY) -> QUERY:
        if op == FTS5.NOT:
            return NOT(left, right)
        klass = {FTS5.AND: AND, FTS5.OR: OR}[op]
        if isinstance(left, klass):
            left.queries.append(right)
            return left
        return klass([left, right])
