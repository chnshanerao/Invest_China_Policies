"""
Multi-source signal collection: gov.cn documents, statistics, enhanced news.
Signals are stored in policy_signals table for LLM consumption.
"""
import asyncio
import logging
import re
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aiohttp
from bs4 import BeautifulSoup

from database import get_connection

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# Per-domain rate limit: seconds between requests
DOMAIN_RATE = {
    "www.gov.cn": 4,
    "stats.gov.cn": 4,
    "default": 3,
}


def _domain_of(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1) if m else "default"


class SignalCollector:
    def __init__(self, rate_limit_seconds: float = 3.0):
        self._rate_limit = rate_limit_seconds
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._domain_last: dict[str, float] = {}

    async def _fetch(self, session: aiohttp.ClientSession, url: str, timeout: int = 15) -> str | None:
        domain = _domain_of(url)
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        lock = self._domain_locks[domain]
        async with lock:
            last = self._domain_last.get(domain, 0)
            wait = DOMAIN_RATE.get(domain, self._rate_limit) - (asyncio.get_event_loop().time() - last)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    self._domain_last[domain] = asyncio.get_event_loop().time()
                    if resp.status == 200:
                        return await resp.text(errors="ignore")
                    logger.warning(f"HTTP {resp.status} for {url}")
                    return None
            except Exception as e:
                logger.warning(f"Fetch error {url}: {e}")
                self._domain_last[domain] = asyncio.get_event_loop().time()
                return None

    async def collect_gov_documents(
        self, session: aiohttp.ClientSession, policy_name: str, policy_document_url: str | None = None
    ) -> list[dict]:
        """Search gov.cn for recent policy documents related to this policy."""
        signals = []

        # Search gov.cn policy database
        search_url = (
            f"https://sousuo.www.gov.cn/sousuo/search.shtml?dataTypeId=107&searchWord="
            f"{aiohttp.helpers.requote_uri(policy_name)}&timetype=time_1year"
        )
        html = await self._fetch(session, search_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select(".result-item, .search-result li")[:5]:
                title_el = item.select_one("a, h3, .title")
                title = title_el.get_text(strip=True) if title_el else ""
                link = title_el.get("href", "") if title_el else ""
                summary_el = item.select_one("p, .summary, .desc")
                summary = summary_el.get_text(strip=True)[:400] if summary_el else ""
                date_el = item.select_one(".date, time, .pubtime")
                date_str = date_el.get_text(strip=True) if date_el else ""
                if title:
                    signals.append({
                        "type": "gov_document",
                        "source": search_url,
                        "title": title[:200],
                        "content": f"{title}\n{summary}",
                        "date": date_str,
                        "url": link,
                    })

        # Also fetch the known policy document URL if available
        if policy_document_url and "gov.cn" in policy_document_url:
            html = await self._fetch(session, policy_document_url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                content_el = soup.select_one("#UCAP-CONTENT, .article-content, .pages_content")
                if content_el:
                    text = content_el.get_text(strip=True)[:800]
                    signals.append({
                        "type": "gov_document",
                        "source": policy_document_url,
                        "title": f"政策原文：{policy_name}",
                        "content": text,
                        "date": "",
                    })

        return signals

    async def collect_statistics(
        self, session: aiohttp.ClientSession, policy_name: str, region: str | None = None
    ) -> list[dict]:
        """Fetch statistical data from NBS and regional bureaus."""
        signals = []
        # National Bureau of Statistics press release search
        nbs_url = (
            f"https://www.stats.gov.cn/sj/zxfb/?searchWord={aiohttp.helpers.requote_uri(policy_name)}"
        )
        html = await self._fetch(session, nbs_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("li, .list-item")[:3]:
                a = item.select_one("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                date_el = item.select_one("span, .date")
                date_str = date_el.get_text(strip=True) if date_el else ""
                signals.append({
                    "type": "statistics",
                    "source": nbs_url,
                    "title": title[:200],
                    "content": f"国家统计局数据：{title}",
                    "date": date_str,
                })
        return signals

    async def collect_enhanced_news(
        self, session: aiohttp.ClientSession, policy_name: str
    ) -> list[dict]:
        """Enhanced Baidu news collection (more items, better parsing)."""
        signals = []
        url = (
            f"https://www.baidu.com/s?wd={aiohttp.helpers.requote_uri(policy_name)}"
            f"+政策+进展&rtt=1&bsst=1&cl=2&tn=news"
        )
        html = await self._fetch(session, url)
        if not html:
            return signals

        soup = BeautifulSoup(html, "html.parser")
        for item in soup.select(".result, [tpl='news_article']")[:8]:
            title_el = item.select_one("h3 a, .news-title a, a.c-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)[:200]
            if not title:
                continue
            summary_el = item.select_one(".c-summary, .news-summary, p")
            summary = summary_el.get_text(strip=True)[:400] if summary_el else ""
            date_el = item.select_one(".c-color-gray, .news-time, time")
            date_str = date_el.get_text(strip=True) if date_el else ""
            link = title_el.get("href", "")
            signals.append({
                "type": "news_cluster",
                "source": link or url,
                "title": title,
                "content": f"{title}\n{summary}",
                "date": date_str,
            })
        return signals

    async def collect_leadership_signals(
        self, session: aiohttp.ClientSession, policy_name: str
    ) -> list[dict]:
        """Check for leadership mentions (State Council, Politburo) of this policy."""
        signals = []
        url = (
            f"https://sousuo.www.gov.cn/sousuo/search.shtml?dataTypeId=107"
            f"&searchWord={aiohttp.helpers.requote_uri(policy_name)}+国务院&timetype=time_1year"
        )
        html = await self._fetch(session, url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select(".result-item")[:3]:
                title_el = item.select_one("a, .title")
                title = title_el.get_text(strip=True) if title_el else ""
                if title and any(kw in title for kw in ["国务院", "政治局", "总书记", "国常会", "中央"]):
                    signals.append({
                        "type": "leadership_mention",
                        "source": url,
                        "title": title[:200],
                        "content": title,
                        "date": "",
                    })
        return signals

    async def collect_all_signals_for_policy(
        self,
        session: aiohttp.ClientSession,
        policy_id: int,
        policy_name: str,
        policy_document_url: str | None = None,
        region: str | None = None,
    ) -> int:
        """Collect all signal types for one policy, insert into policy_signals. Returns count."""
        all_signals: list[dict] = []
        try:
            gov_docs, stats, news, leadership = await asyncio.gather(
                self.collect_gov_documents(session, policy_name, policy_document_url),
                self.collect_statistics(session, policy_name, region),
                self.collect_enhanced_news(session, policy_name),
                self.collect_leadership_signals(session, policy_name),
                return_exceptions=True,
            )
            for result in [gov_docs, stats, news, leadership]:
                if isinstance(result, list):
                    all_signals.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Signal collector error for {policy_name}: {result}")
        except Exception as e:
            logger.error(f"collect_all_signals_for_policy failed for {policy_name}: {e}")

        if not all_signals:
            return 0

        conn = get_connection()
        cursor = conn.cursor()
        inserted = 0
        for sig in all_signals:
            # Deduplicate by title+policy_id
            existing = cursor.execute(
                "SELECT id FROM policy_signals WHERE policy_id=? AND signal_title=?",
                (policy_id, sig.get("title", "")[:200]),
            ).fetchone()
            if existing:
                continue
            cursor.execute(
                """INSERT INTO policy_signals
                   (policy_id, signal_type, signal_source, signal_title, signal_content, signal_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    policy_id,
                    sig["type"],
                    sig["source"][:500],
                    (sig.get("title") or "")[:200],
                    (sig.get("content") or "")[:2000],
                    sig.get("date", ""),
                ),
            )
            inserted += 1
        conn.commit()
        conn.close()
        logger.info(f"  [{policy_name}] inserted {inserted} new signals")
        return inserted

    async def collect_all_policies(self, policies: list[dict], rate_limit: float = 3.0) -> int:
        """Collect signals for all policies. Returns total signals inserted."""
        total = 0
        connector = aiohttp.TCPConnector(limit=5, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            for p in policies:
                count = await self.collect_all_signals_for_policy(
                    session,
                    p["id"],
                    p["name"],
                    p.get("policy_document_url"),
                    p.get("region"),
                )
                total += count
                await asyncio.sleep(rate_limit)
        return total
