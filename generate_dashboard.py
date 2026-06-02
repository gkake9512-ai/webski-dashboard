import requests
import json
import os
from datetime import datetime

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID  = "373622c0b6c9812e9836f994d0c72fba"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

CATEGORIES = ["マニュアルタスク", "作業タスク", "作成タスク"]
STATUS_ORDER = ["未着手", "進行中", "確認待ち", "完了", "保留"]

def get_all_tasks():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    tasks, payload = [], {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        data = r.json()
        tasks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return tasks

def parse_tasks(tasks):
    stats = {cat: {s: 0 for s in STATUS_ORDER} for cat in CATEGORIES}
    for task in tasks:
        props = task.get("properties", {})
        cat_prop = props.get("カテゴリ", {}).get("select")
        cat = cat_prop["name"] if cat_prop else None
        status_prop = props.get("ステータス", {}).get("status")
        status = status_prop["name"] if status_prop else "未着手"
        if cat in stats:
            stats[cat][status if status in STATUS_ORDER else "未着手"] += 1
    return stats

def generate_html(stats):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    total_all = sum(sum(v.values()) for v in stats.values())
    done_all  = sum(v.get("完了", 0) for v in stats.values())
    pct_all   = round(done_all / total_all * 100) if total_all > 0 else 0

    cat_config = {
        "マニュアルタスク": {"icon": "📘", "color": "#378ADD", "bg": "#E6F1FB", "text": "#0C447C"},
        "作業タスク":       {"icon": "🔧", "color": "#EF9F27", "bg": "#FAEEDA", "text": "#633806"},
        "作成タスク":       {"icon": "✏️", "color": "#639922", "bg": "#EAF3DE", "text": "#27500A"},
    }
    status_config = {
        "未着手":   {"bg": "#E6F1FB", "text": "#185FA5"},
        "進行中":   {"bg": "#EAF3DE", "text": "#3B6D11"},
        "確認待ち": {"bg": "#FAEEDA", "text": "#854F0B"},
        "完了":     {"bg": "#E1F5EE", "text": "#0F6E56"},
        "保留":     {"bg": "#FCEBEB", "text": "#A32D2D"},
    }

    cat_cards = ""
    for cat in CATEGORIES:
        s = stats[cat]
        total = sum(s.values())
        done  = s.get("完了", 0)
        pct   = round(done / total * 100) if total > 0 else 0
        cfg   = cat_config[cat]

        badges = ""
        for st in STATUS_ORDER:
            scfg = status_config[st]
            badges += f'<span class="badge" style="background:{scfg["bg"]};color:{scfg["text"]}"><span class="dot" style="background:{scfg["text"]}"></span>{st} {s.get(st,0)}</span>'

        cat_cards += f"""
        <div class="cat-card">
            <div class="cat-header">
                <div class="cat-name">{cfg["icon"]} {cat}</div>
                <div class="cat-right">
                    <span class="cat-count">{total}件</span>
                    <span class="cat-pct" style="color:{cfg["color"]}">{pct}%</span>
                </div>
            </div>
            <div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{cfg["color"]}"></div></div>
            <div class="badges">{badges}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Webski タスク進捗ダッシュボード</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;background:#f5f5f0;padding:20px;color:#1a1a1a}}
  .container{{max-width:680px;margin:0 auto}}
  h1{{font-size:18px;font-weight:500;margin-bottom:4px}}
  .updated{{font-size:12px;color:#888;margin-bottom:20px}}
  .metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}}
  .metric{{background:#fff;border-radius:10px;padding:14px;text-align:center}}
  .metric-label{{font-size:11px;color:#888;margin-bottom:4px}}
  .metric-val{{font-size:22px;font-weight:500}}
  .cat-card{{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px}}
  .cat-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}}
  .cat-name{{font-size:14px;font-weight:500}}
  .cat-right{{display:flex;align-items:center;gap:10px}}
  .cat-count{{font-size:12px;color:#888}}
  .cat-pct{{font-size:14px;font-weight:500}}
  .bar-bg{{height:8px;background:#f0f0ec;border-radius:4px;overflow:hidden;margin-bottom:10px}}
  .bar-fill{{height:100%;border-radius:4px;transition:width .3s}}
  .badges{{display:flex;gap:6px;flex-wrap:wrap}}
  .badge{{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:20px;font-size:11px;font-weight:500}}
  .dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
  .overall{{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px}}
  .overall-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
  .overall-title{{font-size:14px;font-weight:500}}
  .overall-pct{{font-size:20px;font-weight:500;color:#1D9E75}}
</style>
</head>
<body>
<div class="container">
  <h1>📊 Webski タスク進捗ダッシュボード</h1>
  <div class="updated">最終更新：{now}（30分ごと自動更新）</div>

  <div class="metrics">
    <div class="metric"><div class="metric-label">総タスク数</div><div class="metric-val">{total_all}</div></div>
    <div class="metric"><div class="metric-label">未着手</div><div class="metric-val" style="color:#185FA5">{sum(v.get("未着手",0) for v in stats.values())}</div></div>
    <div class="metric"><div class="metric-label">進行中</div><div class="metric-val" style="color:#3B6D11">{sum(v.get("進行中",0) for v in stats.values())}</div></div>
    <div class="metric"><div class="metric-label">完了</div><div class="metric-val" style="color:#0F6E56">{done_all}</div></div>
  </div>

  <div class="overall">
    <div class="overall-header">
      <span class="overall-title">全体進捗</span>
      <span class="overall-pct">{pct_all}%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill" style="width:{pct_all}%;background:#1D9E75"></div></div>
    <div style="font-size:12px;color:#888;text-align:right">{done_all} / {total_all} 件完了</div>
  </div>

  {cat_cards}
</div>
</body>
</html>"""

if __name__ == "__main__":
    tasks = get_all_tasks()
    stats = parse_tasks(tasks)
    html  = generate_html(stats)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html 生成完了")
