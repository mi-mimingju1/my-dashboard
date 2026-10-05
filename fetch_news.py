"""관심 주제별 최신 뉴스를 구글 뉴스 RSS에서 모아 data.json으로 저장합니다.
외부 라이브러리가 필요 없고, 요금도 들지 않습니다."""

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# 관심 주제와 검색어: 여기만 고치면 주제를 바꿀 수 있어요.
TOPICS = {
    "부동산 정책": "부동산 정책",
    "반도체": "반도체",
    "AI": "인공지능 AI",
    "양자컴퓨터": "양자컴퓨터",
    "청약": "청약",
}
PER_TOPIC = 6  # 주제당 기사 수
KST = timezone(timedelta(hours=9))


def feed_url(query):
    q = urllib.parse.quote(query + " when:2d")  # 최근 2일 기사만
    return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"


def parse_feed(xml_bytes, limit=PER_TOPIC):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        # 구글 뉴스 제목은 "기사 제목 - 언론사" 형태라서 뒤쪽 언론사 이름을 떼어 냅니다.
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)]
        date = ""
        pub = it.findtext("pubDate")
        if pub:
            try:
                date = parsedate_to_datetime(pub).astimezone(KST).strftime("%m-%d %H:%M")
            except Exception:
                pass
        if title and link:
            items.append({"title": title, "source": source, "date": date, "url": link})
        if len(items) >= limit:
            break
    return items


def fetch(query):
    req = urllib.request.Request(feed_url(query), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return parse_feed(r.read())


def main():
    topics = {}
    for name, query in TOPICS.items():
        try:
            topics[name] = fetch(query)
        except Exception as e:  # 한 주제가 실패해도 나머지는 계속 진행
            print(f"[경고] {name} 수집 실패: {e}")
            topics[name] = []

    # 오늘의 뉴스 정리: 지금은 주제별 첫 기사를 뽑아 보여줍니다. (나중에 AI 요약으로 교체)
    briefing = []
    for name, arts in topics.items():
        if arts:
            a = arts[0]
            briefing.append({
                "title": a["title"],
                "summary": f"[{name}] 관련 주요 기사",
                "source": a["source"],
                "url": a["url"],
            })

    data = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "briefing": briefing,
        "topics": topics,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json 저장 완료:", {k: len(v) for k, v in topics.items()})


if __name__ == "__main__":
    main()
