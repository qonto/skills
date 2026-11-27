"""Render the local cash simulator without treating account data as HTML."""

import argparse
import json
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "cash-simulator.html"
START = '<script id="sim-data" type="application/json">'
END = '</script>'


def render(data):
    template = TEMPLATE.read_text(encoding="utf-8")
    prefix, rest = template.split(START, 1)
    _, suffix = rest.split(END, 1)
    # HTML parsers recognise </script> even inside a JSON string.
    serialized = json.dumps(data, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c')
    return prefix + START + serialized + END + suffix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="Assessment JSON file")
    parser.add_argument("output", type=Path, help="New local HTML file (never overwritten)")
    args = parser.parse_args()
    html = render(json.loads(args.data.read_text(encoding="utf-8")))
    with args.output.open("x", encoding="utf-8") as output:
        output.write(html)


if __name__ == "__main__":
    main()
