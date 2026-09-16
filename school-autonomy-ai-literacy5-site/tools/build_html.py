from __future__ import annotations

import html
import io
import re
import sys
from pathlib import Path

import pdfplumber
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "docs" / "[붙임3] 학교자율시간 과목 신설 승인 신청서_5학년(청주소로초)_0915.pdf"


def color_value(value: object, fallback: str = "#111") -> str:
    if not isinstance(value, (tuple, list)) or len(value) < 3:
        return fallback
    channels = [max(0, min(255, round(float(channel) * 255))) for channel in value[:3]]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def vector_html(page_number: int) -> str:
    with pdfplumber.open(SOURCE) as pdf:
        page = pdf.pages[page_number - 1]
        elements: list[str] = []
        seen: set[tuple[object, ...]] = set()

        for rect in page.rects:
            width = float(rect.get("width", 0))
            height = float(rect.get("height", 0))
            if width < 4 or height < 2:
                continue
            key = (
                "rect",
                round(float(rect["x0"]), 1),
                round(float(rect["top"]), 1),
                round(width, 1),
                round(height, 1),
            )
            if key in seen:
                continue
            seen.add(key)
            fill = color_value(rect.get("non_stroking_color"), "none")
            stroke = color_value(rect.get("stroking_color"), "#111")
            elements.append(
                f'<rect x="{key[1]}" y="{key[2]}" width="{key[3]}" height="{key[4]}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="0.55"/>'
            )

        for line in page.lines:
            x0 = float(line["x0"])
            x1 = float(line["x1"])
            top = float(line["top"])
            bottom = float(line["bottom"])
            horizontal = abs(bottom - top) < 0.5 and abs(x1 - x0) > 20
            vertical = abs(x1 - x0) < 0.5 and abs(bottom - top) > 20
            if not (horizontal or vertical):
                continue
            key = (
                "line",
                round(x0, 1),
                round(top, 1),
                round(x1, 1),
                round(bottom, 1),
            )
            if key in seen:
                continue
            seen.add(key)
            stroke = color_value(line.get("stroking_color"), "#111")
            elements.append(
                f'<line x1="{key[1]}" y1="{key[2]}" x2="{key[3]}" y2="{key[4]}" '
                f'stroke="{stroke}" stroke-width="0.55"/>'
            )

    return '<svg class="page-vectors" viewBox="0 0 595 841" aria-hidden="true">' + "".join(elements) + "</svg>"


def page_html(page_number: int) -> str:
    stream = io.BytesIO()
    with SOURCE.open("rb") as source:
        extract_text_to_fp(
            source,
            stream,
            laparams=LAParams(),
            output_type="html",
            codec="utf-8",
            page_numbers=[page_number - 1],
        )

    generated = stream.getvalue().decode("utf-8", errors="replace")
    match = re.search(r"<body>(.*)</body>", generated, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"PDF {page_number}쪽의 HTML 본문을 찾지 못했습니다.")
    body = match.group(1)

    body = re.sub(
        r'<div style="position:absolute; top:%dpx;">.*?</div>',
        "",
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r'<div style="position:absolute; top:0px;">Page:.*?</div>',
        "",
        body,
        flags=re.DOTALL,
    )
    body = body.replace("border: textbox 1px solid; ", "")
    body = re.sub(
        r'<span style="position:absolute; border: [^"]+;"></span>\s*',
        "",
        body,
    )

    body = re.sub(
        r'<span[^>]*font-family: Marlett;[^>]*>gfedcb\s*(?:<br>)?\s*</span>',
        '<span class="check checked" aria-label="선택됨"></span>',
        body,
    )
    body = re.sub(
        r'<span[^>]*font-family: Marlett;[^>]*>gfedc\s*(?:<br>)?\s*</span>',
        '<span class="check" aria-label="선택되지 않음"></span>',
        body,
    )

    body = re.sub(
        r"font-family: [^;\"]+;",
        "font-family: 'Batang', 'KoPub Batang', serif;",
        body,
    )
    body = body.replace("writing-mode:lr-tb; ", "")

    if "gfedc" in body:
        raise RuntimeError(f"PDF {page_number}쪽에 변환되지 않은 체크 기호가 남아 있습니다.")

    return f'''<section class="page-shell" aria-label="{page_number}쪽">
      <div class="page-canvas">
        {vector_html(page_number)}
        <div class="generated-page">{body}</div>
      </div>
    </section>'''


title = "학교자율시간 과목 신설 승인 신청서"

if len(sys.argv) == 2:
    print(page_html(int(sys.argv[1])))
    raise SystemExit(0)

pages = "\n".join(page_html(number) for number in range(1, 13))

print(f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(title)}">
  <meta name="theme-color" content="#25282d">
  <title>{html.escape(title)}</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%232d286f'/%3E%3Cpath d='M17 13h30v38H17z' fill='white'/%3E%3Cpath d='M23 23h18M23 31h18M23 39h12' stroke='%232d286f' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="./styles.css">
</head>
<body>
  <main class="document" aria-label="{html.escape(title)}">
{pages}
  </main>
  <script src="./app.js"></script>
</body>
</html>''')
