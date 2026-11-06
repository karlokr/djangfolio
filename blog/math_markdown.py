"""Markdown with LaTeX math, using Pandoc's rules for ``$`` delimiters.

Math is pulled out of the source before Markdown runs (Markdown would treat
backslashes as escapes and underscores as emphasis) and put back afterwards as
``\\(…\\)`` (inline) or ``\\[…\\]`` (display), the only delimiters KaTeX
auto-render is configured for (see ``renderBlogMath`` in base_layout.html).

Recognised math:

* ``$$…$$`` and ``\\[…\\]``: display math, may span lines.
* ``\\(…\\)``: inline math on one line.
* ``$…$``: inline math under Pandoc's ``tex_math_dollars`` rules (also used by
  GitHub and KaTeX auto-render): the opening ``$`` must be followed by a
  non-space character, the closing ``$`` must be preceded by a non-space
  character and not followed by a digit, and the math can't contain an
  unescaped ``$`` or a blank line.  So ``$100``, ``$5 and $10``, ``$HACHI``
  and ``$1.5M`` stay text.

``\\$`` outside math is a literal dollar sign.  Code spans and fenced code
blocks are left exactly as written.
"""
import re
from html import escape

from markdownx.utils import markdownify

_FENCE_OPEN = re.compile(r' {0,3}(`{3,}|~{3,})')
_BACKTICKS = re.compile(r'`+')
_BLANK_LINE = re.compile(r'\n[ \t]*\n')


def markdownify_with_math(content):
    """Convert Markdown to HTML, keeping LaTeX math intact for KaTeX."""
    placeholders = {}

    def placeholder(math, display):
        key = f'MATHBLOCK{len(placeholders)}ENDMATH'
        math = escape(math, quote=False)
        placeholders[key] = f'\\[{math}\\]' if display else f'\\({math}\\)'
        return key

    out = []
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]

        # Fenced code block: copy through to the closing fence.
        if i == 0 or content[i - 1] == '\n':
            fence = _FENCE_OPEN.match(content, i)
            if fence:
                marker = fence.group(1)
                close = re.compile(
                    r'\n {0,3}' + re.escape(marker[0]) + '{' + str(len(marker)) + r',}[ \t]*(?=\n|$)'
                )
                end = close.search(content, fence.end())
                end = end.end() if end else n
                out.append(content[i:end])
                i = end
                continue

        if ch == '`':
            # Code span: a backtick run closed by a run of the same length.
            run = _BACKTICKS.match(content, i).group(0)
            j = i + len(run)
            while True:
                m = _BACKTICKS.search(content, j)
                if not m or m.group(0) == run:
                    break
                j = m.end()
            end = m.end() if m else i + len(run)
            out.append(content[i:end])
            i = end
            continue

        if ch == '\\':
            nxt = content[i + 1:i + 2]
            if nxt == '$':
                out.append('$')
                i += 2
                continue
            if nxt == '(':
                end = content.find('\\)', i + 2)
                if end != -1 and '\n' not in content[i + 2:end]:
                    out.append(placeholder(content[i + 2:end], display=False))
                    i = end + 2
                    continue
            elif nxt == '[':
                end = content.find('\\]', i + 2)
                if end != -1:
                    out.append(placeholder(content[i + 2:end], display=True))
                    i = end + 2
                    continue
            # Any other escape (``\\``, ``\```…) passes through to Markdown.
            out.append(content[i:i + 2])
            i += 2
            continue

        if ch == '$':
            if content.startswith('$$', i):
                end = content.find('$$', i + 2)
                if end > i + 2:
                    out.append(placeholder(content[i + 2:end], display=True))
                    i = end + 2
                else:
                    out.append('$$')
                    i += 2
                continue
            end = _inline_dollar_end(content, i)
            if end is not None:
                out.append(placeholder(content[i + 1:end], display=False))
                i = end + 1
            else:
                out.append('$')
                i += 1
            continue

        out.append(ch)
        i += 1

    html = markdownify(''.join(out))
    return re.sub(r'MATHBLOCK\d+ENDMATH', lambda m: placeholders.get(m.group(0), m.group(0)), html)


def _inline_dollar_end(content, start):
    """Index of the ``$`` closing inline math opened at *start*, or None."""
    n = len(content)
    if start + 1 >= n or content[start + 1].isspace():
        return None
    j = start + 1
    while j < n:
        ch = content[j]
        if ch == '\\':
            j += 2
            continue
        if ch == '$':
            break
        if ch == '\n' and _BLANK_LINE.match(content, j):
            return None
        j += 1
    else:
        return None
    if content[j - 1].isspace():
        return None
    if j + 1 < n and content[j + 1].isdigit():
        return None
    return j
