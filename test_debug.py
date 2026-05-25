from src.crawl.search_announcements import classify_announcement

titles = [
    '关于双汇转债转股价格向下修正的股东大会决议公告',
    '转股价格调整决议公告',
    '关于转股价格调整的公告'
]

for title in titles:
    result = classify_announcement(title)
    print("%s -> %s" % (title, result))