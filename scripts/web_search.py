#!/usr/bin/env python3
"""
web_search.py — 3 层 fallback 搜索引擎,绕开 web_search 工具链.

为什么需要这个脚本:
  - Hermes Agent 的 web_search 工具依赖后端配置,常因 .env 没 source、
    ddgs 包没装、toolset 白名单没显式开而「静默消失」(实测案例:2026-06-28
    debugging arbitrage-radar,3 次说不可用最后发现是 toolset 名写错)
  - 买个 skill 的人,环境千差万别,不能假设 web_search 工具一定可用
  - skill 应该自带 fallback 脚本,这样:
      配 Tavily key → 走 Tavily(快/稳/付费额度 1000/月)
      没 Tavily 但装了 ddgs → 走 ddgs
      啥都没装 → curl DDG HTML(总有一个能跑)

使用方式(在 terminal 里跑):
  python scripts/web_search.py "Fiverr product photography price 2025" --num 5
  python scripts/web_search.py "小红书 买手 月入" --num 3 --backend ddgs

返回(JSON 到 stdout):
  {"query": "...", "backend_used": "tavily|ddgs|ddg_html|none",
   "results": [{"title":..., "url":..., "snippet":...}],
   "errors": ["tavily: ...", "ddgs: ..."]}  # 记录降级链上每一步的失败
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


HERMES_ENV = Path.home() / ".hermes" / ".env"


def _load_hermes_env() -> None:
    """手动 source ~/.hermes/.env(系统 shell 不会自动加载).

    这是 web_search 工具链「静默消失」最常见的原因:key 在 .env 里,
    但当前 shell 没 source,os.environ.get() 返回空。
    """
    if not HERMES_ENV.exists():
        return
    for line in HERMES_ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        # 去引号
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        os.environ.setdefault(k, v)


# ---------------------------------------------------------------------------
# Backend 1: Tavily(优先,有 key 就走,快 + 准)
# ---------------------------------------------------------------------------
def search_tavily(query: str, num: int) -> list[dict[str, str]]:
    """调 Tavily Search API,无需 web_search 工具链."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not set in ~/.hermes/.env")

    import requests  # 延迟导入,避免硬依赖

    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": num,
            "search_depth": "basic",
            "include_answer": False,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
            "source": "tavily",
        }
        for r in data.get("results", [])
    ]


# ---------------------------------------------------------------------------
# Backend 2: ddgs(Python 包,免费,DuckDuckGo 抓取,无需 key)
# ---------------------------------------------------------------------------
def search_ddgs(query: str, num: int) -> list[dict[str, str]]:
    """用 ddgs(新版)/duckduckgo_search(旧版)Python 包.

    新旧包导入路径不同,试两个,旧版常被 Bing 限流,优先用 ddgs.
    """
    try:
        from ddgs import DDGS  # 新包
        impl = "ddgs"
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # 旧包,被限流概率高
            impl = "duckduckgo_search"
        except ImportError as e:
            raise RuntimeError(
                "Neither `ddgs` nor `duckduckgo_search` is installed. "
                "Install with: pip install --user ddgs"
            ) from e

    out: list[dict[str, str]] = []
    with DDGS() as d:
        for r in d.text(query, max_results=num):
            out.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href") or r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "source": impl,
                }
            )
    if not out:
        raise RuntimeError(f"{impl} returned 0 results (likely rate-limited)")
    return out


# ---------------------------------------------------------------------------
# Backend 3: curl DDG HTML(纯 stdlib + curl,任何 Python 环境都能跑)
# ---------------------------------------------------------------------------
def search_ddg_html(query: str, num: int) -> list[dict[str, str]]:
    """抓 DuckDuckGo HTML 端点,用 stdlib html.parser 解析,无需额外 Python 包.

    已知问题:DDG 对 curl UA 也会限流,所以这是最后一道 fallback.
    """
    import html
    import re
    import urllib.parse
    import urllib.request

    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")

    # DDG HTML 结果在 <a class="result__a" href="...">title</a> + .result__snippet
    titles_urls = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        raw,
        re.DOTALL,
    )
    snippets = re.findall(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        raw,
        re.DOTALL,
    )

    out: list[dict[str, str]] = []
    for i, (href, title_html) in enumerate(titles_urls[:num]):
        title = re.sub(r"<[^>]+>", "", title_html)
        title = html.unescape(title).strip()
        snip_html = snippets[i] if i < len(snippets) else ""
        snip = re.sub(r"<[^>]+>", "", snip_html)
        snip = html.unescape(snip).strip()
        out.append(
            {"title": title, "url": href, "snippet": snip, "source": "ddg_html"}
        )

    if not out:
        raise RuntimeError("ddg_html returned 0 results (likely blocked / captcha)")
    return out


# ---------------------------------------------------------------------------
# 主流程:按顺序试,任一成功即返回
# ---------------------------------------------------------------------------
BACKEND_ORDER = ("tavily", "ddgs", "ddg_html")
HANDLERS = {
    "tavily": search_tavily,
    "ddgs": search_ddgs,
    "ddg_html": search_ddg_html,
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query", help="搜索关键词")
    p.add_argument("--num", type=int, default=5, help="返回结果数(默认 5)")
    p.add_argument(
        "--backend",
        choices=BACKEND_ORDER,
        help="强制指定后端(默认按 tavily → ddgs → ddg_html 顺序试)",
    )
    p.add_argument(
        "--quiet", action="store_true", help="不打印降级过程的 stderr 警告"
    )
    args = p.parse_args()

    _load_hermes_env()

    errors: list[str] = []
    backends_to_try = (args.backend,) if args.backend else BACKEND_ORDER

    for backend in backends_to_try:
        try:
            results = HANDLERS[backend](args.query, args.num)
            print(
                json.dumps(
                    {
                        "query": args.query,
                        "backend_used": backend,
                        "num_requested": args.num,
                        "num_returned": len(results),
                        "results": results,
                        "errors": errors,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        except Exception as e:  # noqa: BLE001 — 任何异常都视为该层失败,继续降级
            msg = f"{backend}: {type(e).__name__}: {e}"
            errors.append(msg)
            if not args.quiet:
                print(f"[web_search] {msg} → trying next backend", file=sys.stderr)

    # 全部失败
    print(
        json.dumps(
            {
                "query": args.query,
                "backend_used": "none",
                "num_requested": args.num,
                "num_returned": 0,
                "results": [],
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
