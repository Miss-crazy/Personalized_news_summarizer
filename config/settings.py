"""
config/settings.py
Central configuration. All tunable values live here.
Add/remove RSS feeds and scrape targets freely.
"""
 
import os
from dotenv import load_dotenv
 
load_dotenv()
 
# ── API keys ────────────────────────────────────────────────
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
 
# ── Storage ─────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "data/news.db")
 
# ── GNews settings ──────────────────────────────────────────
GNEWS_MAX_ARTICLES = int(os.getenv("GNEWS_MAX_ARTICLES", 10))
 
# GNews topics to pull (free tier supports one call per topic)
# Full list: world, nation, business, technology, entertainment,
#            sports, science, health
GNEWS_TOPICS = [
    "technology",
    "business",
    "science",
    "health",
    "sports",
]
 
# ── RSS feeds ───────────────────────────────────────────────
# Add any RSS/Atom feed URL here. Label is used for source tagging.
RSS_FEEDS = [
    {"label": "BBC World",       "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"label": "BBC Technology",  "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"label": "Reuters Top News","url": "https://feeds.reuters.com/reuters/topNews"},
    {"label": "NASA Breaking",   "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"label": "TechCrunch",      "url": "https://techcrunch.com/feed/"},
    {"label": "The Verge",       "url": "https://www.theverge.com/rss/index.xml"},
]
 
# ── Web scrape targets ───────────────────────────────────────
# Each entry needs:
#   url          - page listing article links
#   base_url     - prepended to relative hrefs
#   link_selector- CSS selector that matches <a> tags for articles
#   label        - source name stored in DB
SCRAPE_TARGETS = [
    {
        "label": "Hacker News",
        "url": "https://news.ycombinator.com/",
        "base_url": "",           # HN links are absolute
        "link_selector": ".titleline > a",
    },
    {
        "label": "MIT Tech Review",
        "url": "https://www.technologyreview.com/",
        "base_url": "https://www.technologyreview.com",
        "link_selector": "a.teaserItem__title--3ntdm, h3 > a",
    },
]
 
# ── Scheduler ────────────────────────────────────────────────
# Fast loop  — fetch + dedup + store   (minutes)
FAST_LOOP_INTERVAL_MINUTES = 30
 
# ── Scraper behaviour ────────────────────────────────────────
SCRAPER_MAX_ARTICLES = int(os.getenv("SCRAPER_MAX_ARTICLES", 5))
 
# Polite delay between HTTP requests (seconds)
REQUEST_DELAY_SECONDS = 1.5
 
# Shared request headers (identify bot politely)
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NewsBot/1.0; "
        "+https://github.com/Miss-crazy/news-summarizer)"
    )
}
 
