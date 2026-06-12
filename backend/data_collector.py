import asyncio
import aiohttp
import json
import re
import sqlite3
import os
import sys
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


async def fetch_url(session, url, timeout=15):
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as resp:
            if resp.status == 200:
                return await resp.text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
    return None


async def search_baidu_news(session, keyword, count=5):
    results = []
    url = f"https://www.baidu.com/s?wd={keyword}+最新政策+投资&rtt=1&bsst=1&cl=2&tn=news"
    html = await fetch_url(session, url)
    if not html:
        return results

    soup = BeautifulSoup(html, "html.parser")
    for item in soup.select(".result")[:count]:
        title_tag = item.select_one("h3 a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag.get("href", "")
        summary = ""
        summary_tag = item.select_one(".c-summary, .c-abstract")
        if summary_tag:
            summary = summary_tag.get_text(strip=True)

        date_text = ""
        date_tag = item.select_one(".c-color-gray, .c-color-gray2")
        if date_tag:
            date_text = date_tag.get_text(strip=True)

        sentiment = analyze_sentiment(title + " " + summary)
        results.append({
            "title": title[:200],
            "summary": summary[:500],
            "source": "百度新闻",
            "url": link,
            "published_at": date_text,
            "sentiment": sentiment,
        })

    return results


def analyze_sentiment(text):
    positive_words = ["利好", "增长", "突破", "新高", "加速", "超预期", "上涨", "繁荣", "红利", "机遇", "创新高", "大涨"]
    negative_words = ["下跌", "风险", "亏损", "下滑", "暴跌", "危机", "违约", "暴雷", "处罚", "退市", "收缩", "下降"]
    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    if pos > neg:
        return "积极"
    elif neg > pos:
        return "消极"
    return "中性"


def determine_impact(title, summary):
    text = title + " " + summary
    high_impact = ["国务院", "中央", "总书记", "重大", "万亿", "千亿", "历史性", "首次"]
    medium_impact = ["发改委", "部委", "省级", "百亿", "政策", "规划"]
    for w in high_impact:
        if w in text:
            return "高"
    for w in medium_impact:
        if w in text:
            return "中"
    return "低"


async def collect_news_for_policy(session, policy_id, policy_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        news_items = await search_baidu_news(session, policy_name)
        inserted = 0
        for item in news_items:
            cursor.execute("SELECT COUNT(*) FROM policy_news WHERE policy_id=? AND title=?",
                         (policy_id, item["title"]))
            if cursor.fetchone()[0] == 0:
                impact = determine_impact(item["title"], item["summary"])
                cursor.execute("""
                    INSERT INTO policy_news (policy_id, title, summary, source, url, published_at, sentiment, impact_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (policy_id, item["title"], item["summary"], item["source"],
                      item["url"], item["published_at"], item["sentiment"], impact))
                inserted += 1
        conn.commit()
        logger.info(f"[{policy_name}] Collected {inserted} new news items")
        return inserted
    except Exception as e:
        logger.error(f"Error collecting news for {policy_name}: {e}")
        return 0
    finally:
        conn.close()


async def update_market_data(session, policy_id, instruments):
    if not instruments:
        return
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for code in instruments.split(","):
            code = code.strip()
            if not code:
                continue
            cursor.execute("""
                INSERT INTO market_indicators (policy_id, indicator_name, indicator_value, change_pct, period)
                VALUES (?, ?, NULL, NULL, ?)
            """, (policy_id, f"stock:{code}", datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    finally:
        conn.close()


async def run_full_update():
    log_id = log_update_start("full_update")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name FROM policies p ORDER BY p.id
    """)
    policies = cursor.fetchall()
    conn.close()

    total_news = 0
    async with aiohttp.ClientSession() as session:
        for policy in policies:
            pid, pname = policy["id"], policy["name"]
            count = await collect_news_for_policy(session, pid, pname)
            total_news += count
            await asyncio.sleep(2)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT io.recommended_instruments, io.policy_id
        FROM investment_opportunities io
        WHERE io.recommended_instruments IS NOT NULL AND io.recommended_instruments != ''
    """)
    opps = cursor.fetchall()
    conn.close()

    async with aiohttp.ClientSession() as session:
        for opp in opps:
            await update_market_data(session, opp["policy_id"], opp["recommended_instruments"])

    log_update_end(log_id, total_news)
    logger.info(f"Full update completed. Total new news: {total_news}")
    return total_news


def log_update_start(update_type, policy_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO data_updates (update_type, policy_id, status, started_at)
        VALUES (?, ?, 'running', ?)
    """, (update_type, policy_id, datetime.now().isoformat()))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def log_update_end(log_id, records_updated, error=None):
    conn = get_connection()
    cursor = conn.cursor()
    status = "completed" if not error else "failed"
    cursor.execute("""
        UPDATE data_updates SET status=?, records_updated=?, error_message=?, completed_at=?
        WHERE id=?
    """, (status, records_updated, error, datetime.now().isoformat(), log_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    asyncio.run(run_full_update())
