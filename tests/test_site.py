from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"img", "script"} and attributes.get("src"):
            self.references.append(attributes["src"] or "")
        if tag == "link" and attributes.get("href"):
            self.references.append(attributes["href"] or "")


def test_site_local_assets_exist() -> None:
    index = SITE / "index.html"
    parser = AssetParser()
    parser.feed(index.read_text(encoding="utf-8"))

    missing: list[str] = []
    for reference in parser.references:
        parsed = urlparse(reference)
        if parsed.scheme or reference.startswith("//"):
            continue
        path = SITE / unquote(parsed.path)
        if not path.exists():
            missing.append(reference)

    assert not missing, f"Missing site assets: {missing}"


def test_site_keeps_evidence_boundary_visible() -> None:
    index = (SITE / "index.html").read_text(encoding="utf-8")
    data = (SITE / "data.js").read_text(encoding="utf-8")

    assert "合成 / 算法演示" in index
    assert "不代表名创优品真实经营指标" in index
    assert "synthetic_and_algorithm_demo" in data
    assert "未触发任何生产动作" in (SITE / "app.js").read_text(encoding="utf-8")


def test_site_opens_with_the_decision_story() -> None:
    index = (SITE / "index.html").read_text(encoding="utf-8")

    assert "不是生成更多创意" in index
    assert "而是证明哪两个值得下一步" in index
    assert "4 个候选收敛为 2 个前沿候选" in index
    assert "不代表名创优品真实经营指标" in index
    assert "进入创意前沿" in index
    assert "查看回测证据" in index
