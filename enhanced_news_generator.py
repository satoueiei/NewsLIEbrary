import feedparser
import google.generativeai as genai
import requests
import random
import os
import json
from datetime import datetime, timedelta
import markdown
import re
from random import choice
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asyncio
from twikit import Client

# Geminiと接続
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')
phone=os.environ.get('PHONE')
mail=os.environ.get('MAIL')

client = Client('ja')

def load_articles_json():
    json_path = "docs/articles.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def find_sequel_candidate(articles, days_threshold=30):
    now = datetime.now()
    candidates = []
    for article in articles:
        if "Y" in article.get("sequel","N"):
            article_date = datetime.strptime(article["date"], "%Y-%m-%d")
            days_elapsed = (now - article_date).days
            if days_elapsed >= days_threshold and days_elapsed<days_threshold+30:
                candidates.append(article)
    return choice(candidates) if candidates else None

def generate_news_article():
    feed = feedparser.parse('https://trends.google.co.jp/trending/rss?geo=JP')
    titles = [entry['title'] for entry in feed['entries']]

    Ses = requests.Session()
    URL = "https://ja.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnlimit": "10",
        "rnnamespace": "0"
    }
    R = Ses.get(url=URL, params=PARAMS)
    DATA = R.json()
    RANDOMS = DATA["query"]["random"]
    wiki_title = random.choice(RANDOMS)["title"]

    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")

    personalities = [
        "皮肉屋", "楽観主義者", "陰謀論者", "ドラマチック", "冷静分析家",
        "詩人", "お調子者", "悲観主義者", "科学オタク", "おばちゃん",
        "軍人風", "ヒーロー気取り", "ノスタルジック", "子供っぽい", "哲学者",
        "ゴシップ好き", "クイズマスター", "ファンタジー作家", "ロボット", "探偵",
        "スポーツ実況者", "お笑い芸人", "過激派", "ヒッピー", "ビジネスマン",
        "カウボーイ", "医者", "占い師", "革命家", "オカルト信者",
        "美食家", "映画監督", "教師", "ギャンブラー", "アーティスト",
        "マッドサイエンティスト", "お坊さん", "海賊", "旅行者", "ラッパー",
        "気象予報士", "ゲーム実況者", "スパイ", "お姫様", "ゾンビ",
        "エンジニア", "宇宙人", "タイムトラベラー", "恋愛マスター", "怠け者",
        "ひねくれもの","批評家","厨二病","ヤンデレ","ツンデレ",
        "なんJ民","コンピューターウイルス","陰キャ","変態","上位存在",
        "おじさん構文","チャラ男","ヒステリック","うちなーぐち","関西弁",
        "淫夢厨","陽キャ","原始人","酔っぱらった人","説教",
        "英語","クソガキ","古","激情家","おバカちゃん",
        "普通の記者","炎上系記者","インプ稼ぎ記者","やる気ない記者","熱意ある記者",
        "海外の記者","お嬢様","異世界転生者","昭和の頑固おやじ","ネットミーム中毒者",
        "武士","神父","キリシタン","ずんだもん","ゆっくり実況"
    ]

    theme = random.choice(titles)
    personality = random.choice(personalities)
    
    now = datetime.now()
    date_string = now.strftime("%Y年%m月%d日")
    time_string = now.strftime("%H:%M")
    
    prompt = f"架空のニュースサイト、「News LIE-brary」に載せるための、「{theme}」と「{wiki_title}」をテーマにした架空のネットニュースをマークダウン形式で作ってください。「{personality}」風な文体で、1000~2000字程度を参考に作ってください。タイトルをつけ、タイトルにはニュースサイトの名前を【】で囲んで、h1として必ず記述してください。日付は {date_string} とし、記事の一番上に表示してください。ただし、ニュースサイトのほかの部分でこれが架空であることを示しますので、記事本文にはこれが架空であることを示す内容は入れないことと、回答はニュース記事部分だけにしてください。"
    
    response = model.generate_content(prompt)
    content = response.text

    #続きそうか判定
    question=f"以下のニュース記事の本文を読み、この記事に対して「続報を出す」といったような、続編執筆に対する明確な意思表示が記事内に存在するかどうかを判断してください。記事内に「続報を出す」といった明確な言葉による宣言が存在する場合には「Y」、存在しない場合には「N」とだけ答えてください。記事の内容から推測される今後の展開や、記者の意図に関する解釈は含めないでください。{content}"
    ansewer=model.generate_content(question)
    sequel=ansewer.text
    
    
    

    title_match = re.search(r"^\s*#+\s*【News LIE-brary】[^\n]+", content, re.MULTILINE)
    article_title = title_match.group(0).replace("#", "").strip() if title_match else "無題の記事"
    
    metadata = {
        "date": now.strftime("%Y-%m-%d"),
        "time": time_string,
        "theme": theme,
        "wiki_title": wiki_title,
        "personality": personality,
        "timestamp": now.timestamp(),
        "title": article_title,
        "sequel": sequel
    }
    
    return content, metadata
    
async def generate_news_article2():
    # アカウントにログイン
    client.load_cookies('cookies.json')
    output=await client.get_place_trends(23424856)
    for i in output["trends"]:
        print(i.name)
    xtrend=random.choice(output["trends"]).name

    Ses = requests.Session()
    URL = "https://ja.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnlimit": "10",
        "rnnamespace": "0"
    }
    R = Ses.get(url=URL, params=PARAMS)
    DATA = R.json()
    RANDOMS = DATA["query"]["random"]
    wiki_title = random.choice(RANDOMS)["title"]

    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")

    personalities = [
        "皮肉屋", "楽観主義者", "陰謀論者", "ドラマチック", "冷静分析家",
        "詩人", "お調子者", "悲観主義者", "科学オタク", "おばちゃん",
        "軍人風", "ヒーロー気取り", "ノスタルジック", "子供っぽい", "哲学者",
        "ゴシップ好き", "クイズマスター", "ファンタジー作家", "ロボット", "探偵",
        "スポーツ実況者", "お笑い芸人", "過激派", "ヒッピー", "ビジネスマン",
        "カウボーイ", "医者", "占い師", "革命家", "オカルト信者",
        "美食家", "映画監督", "教師", "ギャンブラー", "アーティスト",
        "マッドサイエンティスト", "お坊さん", "海賊", "旅行者", "ラッパー",
        "気象予報士", "ゲーム実況者", "スパイ", "お姫様", "ゾンビ",
        "エンジニア", "宇宙人", "タイムトラベラー", "恋愛マスター", "怠け者",
        "ひねくれもの","批評家","厨二病","ヤンデレ","ツンデレ",
        "なんJ民","コンピューターウイルス","陰キャ","変態","上位存在",
        "おじさん構文","チャラ男","ヒステリック","うちなーぐち","関西弁",
        "淫夢厨","陽キャ","原始人","酔っぱらった人","説教",
        "英語","クソガキ","古","激情家","おバカちゃん",
        "普通の記者","炎上系記者","インプ稼ぎ記者","やる気ない記者","熱意ある記者",
        "海外の記者","お嬢様","異世界転生者","昭和の頑固おやじ","ネットミーム中毒者",
        "武士","神父","キリシタン","ずんだもん","ゆっくり実況"
    ]

    personality = random.choice(personalities)
    
    now = datetime.now()
    date_string = now.strftime("%Y年%m月%d日")
    time_string = now.strftime("%H:%M")
    
    prompt = f"架空のニュースサイト、「News LIE-brary」に載せるための、「{xtrend}」と「{wiki_title}」をテーマにした架空のネットニュースをマークダウン形式で作ってください。「{personality}」風な文体で、1000~2000字程度を参考に作ってください。タイトルをつけ、タイトルにはニュースサイトの名前を【】で囲んで、h1として必ず記述してください。日付は {date_string} とし、記事の一番上に表示してください。ただし、ニュースサイトのほかの部分でこれが架空であることを示しますので、記事本文にはこれが架空であることを示す内容は入れないことと、回答はニュース記事部分だけにしてください。"
    
    response = model.generate_content(prompt)
    content = response.text

    #続きそうか判定
    question=f"以下のニュース記事の本文を読み、この記事に対して「続報を出す」といったような、続編執筆に対する明確な意思表示が記事内に存在するかどうかを判断してください。記事内に「続報を出す」といった明確な言葉による宣言が存在する場合には「Y」、存在しない場合には「N」とだけ答えてください。記事の内容から推測される今後の展開や、記者の意図に関する解釈は含めないでください。{content}"
    ansewer=model.generate_content(question)
    sequel=ansewer.text
    
    
    

    title_match = re.search(r"^\s*#+\s*【News LIE-brary】[^\n]+", content, re.MULTILINE)
    article_title = title_match.group(0).replace("#", "").strip() if title_match else "無題の記事"
    
    metadata = {
        "date": now.strftime("%Y-%m-%d"),
        "time": time_string,
        "theme": xtrend,
        "wiki_title": wiki_title,
        "personality": personality,
        "timestamp": now.timestamp(),
        "title": article_title,
        "sequel": sequel
    }
    
    return content, metadata
    
def generate_sequel_article(prev_article):
    # 前回の記事内容を読み込む
    prev_url = prev_article["url"]
    prev_md_path = os.path.join("content", prev_url.replace(".html", ".md"))
    with open(prev_md_path, "r", encoding="utf-8") as f:
        prev_content = f.read()

    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    now = datetime.now()
    date_string = now.strftime("%Y年%m月%d日")
    time_string = now.strftime("%H:%M")

    # 続編用のプロンプト
    prompt = f"""架空のニュースサイト、「News LIE-brary」に載せるための、前回の記事「{prev_article['title']}」を参考にした、続報を期待させられる、もしくは続報が出ないと誤解無く判断させられる、架空のネットニュースをマークダウン形式で作ってください。前回の記事の内容は以下です：\n{prev_content}\nテーマは「{prev_article['theme']}」と「{prev_article['wiki_title']}」を引き継ぎ、「{prev_article['personality']}」風の文体で、1000~2000字程度を参考にしてください。タイトルをつけ、タイトルにはニュースサイトの名前を【】で囲んだものと【続報】を、h1として必ず記述してください。日付は {date_string} とし、記事の一番上に表示してください。ただし、前回の記事へのリンクおよびニュースサイトのほかの部分でこれが架空であることを示しますので、記事本文には前回の記事へのリンクと、これが架空であることを示す内容は入れないこととします。回答はニュース記事部分だけにしてください。"""

    response = model.generate_content(prompt)
    content = response.text

    # 続編かどうかの判定
    question = f"以下のニュース記事の本文を読み、この記事に対して「続報を出す」といったような、続編執筆に対する明確な意思表示が記事内に存在するかどうかを判断してください。記事内に「続報を出す」といった明確な言葉による宣言が存在する場合には「Y」、存在しない場合には「N」とだけ答えてください。記事の内容から推測される今後の展開や、記者の意図に関する解釈は含めないでください。\n{content}"
    answer = model.generate_content(question)
    sequel = answer.text

    # メタデータを作成
    metadata = {
        "date": now.strftime("%Y-%m-%d"),
        "time": time_string,
        "theme": prev_article["theme"],
        "wiki_title": prev_article["wiki_title"],
        "personality": prev_article["personality"],
        "timestamp": now.timestamp(),
        "title": re.search(r"^\s*#+\s*【News LIE-brary】[^\n]+", content, re.MULTILINE).group(0).replace("#", "").strip() if re.search(r"^\s*#+\s*【News LIE-brary】[^\n]+", content, re.MULTILINE) else "無題の記事",
        "sequel": sequel,
        "prev_url": prev_article["url"]  # 前回記事へのリンクをメタデータに追加
    }

    # 元の記事のメタデータを更新（"sequel"を"C"に）
    prev_json_path = os.path.join("content", prev_url.replace(".html", ".json"))
    if os.path.exists(prev_json_path):
        with open(prev_json_path, "r", encoding="utf-8") as f:
            prev_metadata = json.load(f)
        prev_metadata["sequel"] = "C"  # 続編作成済みに更新
        with open(prev_json_path, "w", encoding="utf-8") as f:
            json.dump(prev_metadata, f, ensure_ascii=False, indent=2)

    return content, metadata

def save_article(content, metadata):
    base_dir = "content"
    year_dir = os.path.join(base_dir, metadata["date"][:4])
    month_dir = os.path.join(year_dir, metadata["date"][5:7])
    os.makedirs(month_dir, exist_ok=True)
    
    timestamp = metadata["timestamp"]
    filename_base = f"{metadata['date']}-{int(timestamp)}"
    
    content_path = os.path.join(month_dir, f"{filename_base}.md")
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    metadata_path = os.path.join(month_dir, f"{filename_base}.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return content_path, metadata_path

def generate_html_from_markdown(md_content, metadata):
    html_content = markdown.markdown(md_content)
    
    article_title = metadata.get('title', '無題の記事')
    prev_link = f'<p><a href="../../{metadata["prev_url"]}">前回の記事を読む</a></p>' if "prev_url" in metadata else ""

    # articles.jsonから全記事のリストを読み込む
    articles = load_articles_json()
    # タイムスタンプを基準にソート
    sorted_articles = sorted(articles, key=lambda x: x["timestamp"])
    current_url = f"{metadata['date'][:4]}/{metadata['date'][5:7]}/{metadata['date']}-{int(metadata['timestamp'])}.html"
    
    # 現在の記事のインデックスを見つける
    current_index = next((i for i, article in enumerate(sorted_articles) if article["url"] == current_url), -1)
    
    # 前後の記事を特定（タイムスタンプ順）
    prev_article_url = sorted_articles[current_index - 1]["url"] if current_index > 0 else None
    next_article_url = sorted_articles[current_index + 1]["url"] if current_index < len(sorted_articles) - 1 else None

    # ナビゲーションHTMLを生成
    navigation_html = '<div class="article-navigation">'
    if prev_article_url:
        navigation_html += f'<a href="../../{prev_article_url}" class="nav-arrow prev-arrow">◀ 前の記事</a>'
    else:
        navigation_html += '<span class="nav-arrow prev-arrow disabled">◀ 前の記事</span>'
    if next_article_url:
        navigation_html += f'<a href="../../{next_article_url}" class="nav-arrow next-arrow">次の記事 ▶</a>'
    else:
        navigation_html += '<span class="nav-arrow next-arrow disabled">次の記事 ▶</span>'
    navigation_html += '</div>'

    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大滑子帝国広報部 - {article_title}</title>
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{ border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; }}
        footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.8em; color: #666; }}
        .metadata {{ font-size: 0.9em; color: #666; }}
        h1 {{ color: #333; }}
        .archive-link {{ margin-top: 10px; }}
        .article-navigation {{ margin: 20px 0; display: flex; justify-content: space-between; align-items: center; }}
        .nav-arrow {{ padding: 8px 15px; text-decoration: none; color: #0066cc; font-weight: bold; }}
        .nav-arrow.disabled {{ color: #999; pointer-events: none; }}
        .nav-arrow:hover:not(.disabled) {{ text-decoration: underline; background-color: #f5f5f5; border-radius: 5px; }}
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部</h1>
        <p>帝国ニュースサイト「News LIE-brary」が、大滑子帝国の日常をお届けします。</p>
        <p class="archive-link"><a href="../../index.html">アーカイブに戻る</a></p>
        {navigation_html}  <!-- ナビゲーションを本文とメタデータの間に配置 -->
    </header>
    <main>
        <article>
            {html_content}
            {prev_link}
        </article>
        
        <div class="metadata">
            <p>テーマ: {metadata['theme']} x {metadata['wiki_title']}</p>
            <p>文体: {metadata['personality']}風</p>
            <p>生成日時: {metadata['date']} {metadata['time']}</p>
        </div>
    </main>
    <footer>
        {navigation_html}  <!-- ナビゲーションを本文とメタデータの間に配置 -->
        <p>このニュースは自動生成されたフィクションです。実在の人物・団体とは関係ありません。</p>
        <p class="archive-link"><a href="../../index.html">アーカイブに戻る</a></p>
    </footer>
</body>
</html>
"""
    return html_template

def generate_index_page(articles_metadata):
    # 記事メタデータをJSONとして保存する準備（別ファイルに出力）
    sorted_articles = sorted(articles_metadata, key=lambda x: x["timestamp"], reverse=True)
    
    # JSONデータを作成
    articles_json = []
    for article in sorted_articles:
        article_date = article["date"]
        year = article_date[:4]
        month = article_date[5:7]
        filename_base = f"{article_date}-{int(article['timestamp'])}"
        articles_json.append({
            "title": article.get('title', '無題の記事'),
            "url": f"{year}/{month}/{filename_base}.html",
            "date": article_date,
            "personality": article["personality"],
            "timestamp": article["timestamp"],
            "sequel": article.get("sequel","N"),
            "theme": article["theme"],
            "wiki_title": article["wiki_title"]
        })
    
    # JSONファイルとして保存
    with open("docs/articles.json", "w", encoding="utf-8") as f:
        json.dump(articles_json, f, ensure_ascii=False, indent=2)
    
    # コンパクトなindex.htmlテンプレート
    index_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大滑子帝国広報部 - アーカイブ</title>
    <style>
        body { font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.4; max-width: 800px; margin: 0 auto; padding: 10px; }
        header { border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-bottom: 10px; }
        footer { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 5px; font-size: 0.8em; color: #666; }
        ul { list-style-type: none; padding: 0; margin: 0; }
        li { padding: 5px 0; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .filter-container { display: flex; gap: 5px; margin-bottom: 10px; flex-wrap: wrap; } /* flex-wrap追加 */
        #search-bar { width: calc(50% - 5px); padding: 5px; font-size: 0.9em; min-width: 150px; } /* 幅調整 */
        #date-filter { width: calc(25% - 5px); padding: 5px; font-size: 0.9em; min-width: 100px; } /* 幅調整 */
        #persona-filter { width: calc(25% - 5px); padding: 5px; font-size: 0.9em; min-width: 100px; } /* 幅調整 */
        .pagination { margin-top: 10px; text-align: center; }
        .pagination button { padding: 3px 8px; margin: 0 3px; cursor: pointer; }
        .pagination span { margin: 0 5px; font-size: 0.9em; }
        .pagination input { width: 50px; padding: 3px; text-align: center; }
        .bookmark-btn{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 2px 5px;
            cursor: pointer;
            font-size: 0.8em;
            border-radius: 2px;
            margin-left: 5px; /* 左にマージン追加 */
            flex-shrink: 0; /* ボタンが縮まないように */
        }
        .bookmark-btn.bookmarked{
            background: #af4c4c;
            color: white;
            border: none;
            padding: 2px 5px;
            cursor: pointer;
            font-size: 0.8em;
            border-radius: 2px;
            margin-left: 5px; /* 左にマージン追加 */
            flex-shrink: 0; /* ボタンが縮まないように */
        }
        .bookmark-btn:hover { background: #45a049; }
        .bookmark-btn.bookmarked:hover { background: #a04545; }
        a { text-decoration: none; color: #0066cc; word-wrap: break-word; flex-grow: 1; } /* aタグがスペースを埋めるように */
        a:hover { text-decoration: underline; }
        .hidden { display: none; }
        h2 { margin: 10px 0 5px; font-size: 1.2em; color: #333; } /* 日付見出し */
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部</h1>
        <p>「News LIE-brary」として配信されたニュース記事をアーカイブしたものです。</p>
        <p><a href="./bookmark.html">ブックマーク</a></p>
    </header>
    <main>
        <div class="filter-container">
            <input type="text" id="search-bar" placeholder="検索...">
            <select id="date-filter"><option value="">全日付</option></select>
            <select id="persona-filter"><option value="">全文体</option></select>
        </div>
        <div id="article-list"></div>
        <div class="pagination">
            <button id="prev-page" disabled>◀</button>
            <span id="page-info">ページ 1</span>
            <input type="number" id="page-input" min="1" placeholder="ページ">
            <button id="go-page">移動</button>
            <button id="next-page">▶</button>
        </div>
    </main>
    <footer>
        <p>このサイトのニュースはフィクションです。</p>
    </footer>
    <script src="bookmark.js"></script>
    <script>
        const searchBar = document.getElementById('search-bar');
        const dateFilter = document.getElementById('date-filter');
        const personaFilter = document.getElementById('persona-filter'); // persona-filter の typo を修正
        const articleList = document.getElementById('article-list');
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');
        const pageInput = document.getElementById('page-input');
        const goPageBtn = document.getElementById('go-page');

        const itemsPerPage = 100;
        let currentPage = 1;
        let articles = [];
        let dateCounts = {}; // 日付ごとの記事数を格納
        let personaCounts = {}; // 文体ごとの記事数を格納

        fetch('./articles.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTPエラー: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                articles = data;

                // 記事数をカウント
                articles.forEach(a => {
                    dateCounts[a.date] = (dateCounts[a.date] || 0) + 1;
                    personaCounts[a.personality] = (personaCounts[a.personality] || 0) + 1;
                });

                // フィルターオプションを生成（記事数を渡す）
                populateDateFilter(dateCounts);
                populatePersonaFilter(personaCounts);
                renderArticles();
                // addWheelEventToPersonalityFilter(); // この関数は定義されていないためコメントアウト or 実装が必要
            })
            .catch(error => {
                console.error('JSON読み込みエラー:', error);
                articleList.innerHTML = '<p>記事データを読み込めませんでした。</p>';
            });

        /*
        // persona-filterにホイールイベントを追加する関数（必要であれば実装）
        function addWheelEventToPersonalityFilter() {
            personaFilter.addEventListener('wheel', (event) => {
                event.preventDefault(); // デフォルトのスクロール動作を止める

                const currentIndex = personaFilter.selectedIndex; // 現在選ばれてるオプションのインデックス
                const totalOptions = personaFilter.options.length; // オプションの総数

                // ホイールの方向をチェック（上か下か）
                if (event.deltaY < 0) {
                    // 上にスクロール（前のオプションへ）
                    if (currentIndex > 0) {
                        personaFilter.selectedIndex = currentIndex - 1;
                    }
                } else if (event.deltaY > 0) {
                    // 下にスクロール（次のオプションへ）
                    if (currentIndex < totalOptions - 1) {
                        personaFilter.selectedIndex = currentIndex + 1;
                    }
                }

                // 選択が変わったら記事を再描画
                currentPage = 1;
                renderArticles();
            });
        }
        */

        // 日付フィルターに記事数を表示する関数
        function populateDateFilter(counts) {
            const dates = [...new Set(articles.map(a => a.date))].sort().reverse();
            // 既存のオプションをクリア（「全日付」は残す）
            while (dateFilter.options.length > 1) {
                dateFilter.remove(1);
            }
            // 全記事数を「全日付」オプションに表示（任意）
            const totalArticles = articles.length;
            dateFilter.options[0].textContent = `全日付 (${totalArticles}件)`;

            dates.forEach(date => {
                const option = document.createElement('option');
                option.value = date;
                const count = counts[date] || 0;
                option.textContent = `${date} (${count}件)`;
                dateFilter.appendChild(option);
            });
        }

        // 文体フィルターに記事数を表示する関数
        function populatePersonaFilter(counts) {
            const personalities = [...new Set(articles.map(a => a.personality))].sort();
            // 既存のオプションをクリア（「全文体」は残す）
            while (personaFilter.options.length > 1) {
                personaFilter.remove(1);
            }
            // 全記事数を「全文体」オプションに表示（任意）
            const totalArticles = articles.length;
            personaFilter.options[0].textContent = `全文体 (${totalArticles}件)`;

            personalities.forEach(personality => {
                const option = document.createElement('option');
                option.value = personality;
                const count = counts[personality] || 0;
                option.textContent = `${personality} (${count}件)`;
                personaFilter.appendChild(option);
            });
        }

        function renderArticles() {
            const query = searchBar.value.toLowerCase();
            const selectedDate = dateFilter.value;
            const selectedPersona = personaFilter.value;

            const filteredArticles = articles.filter(a => {
                const matchesSearch = query === '' ||
                    a.title.toLowerCase().includes(query) ||
                    a.date.includes(query) ||
                    (a.personality && a.personality.toLowerCase().includes(query)); // personalityが存在するかチェック
                const matchesDate = selectedDate === '' || a.date === selectedDate;
                const matchesPersona = selectedPersona === '' || a.personality === selectedPersona;
                return matchesSearch && matchesDate && matchesPersona;
            });

            const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
            currentPage = Math.max(1, Math.min(currentPage, totalPages || 1)); // フィルター変更時にページ番号を調整
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            const paginatedArticles = filteredArticles.slice(start, end);

            const articlesByDate = {};
            paginatedArticles.forEach(a => {
                if (!articlesByDate[a.date]) articlesByDate[a.date] = [];
                articlesByDate[a.date].push(a);
            });

            articleList.innerHTML = '';
            // 日付でソートして表示
            Object.keys(articlesByDate).sort().reverse().forEach(date => {
                const section = document.createElement('div');
                section.innerHTML = `<h2>${date}</h2>`;
                const ul = document.createElement('ul');
                // 日付内の記事リストを（必要なら）タイトル等でソート
                articlesByDate[date].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));


                    // リンク要素
                    const link = document.createElement('a');
                    link.href = a.url;
                    link.title = `${a.title} (${a.personality || '不明'}風, ${a.date})`;
                    link.textContent = `${a.title} (${a.personality || '不明'}風)`; // personalityがない場合も考慮

                    // ボタン要素
                    const button = document.createElement('button');
                    button.classList.add('bookmark-btn');
                    button.setAttribute('data-title', a.title);
                    button.setAttribute('data-url', a.url);
                    button.setAttribute('data-date', a.date);
                    // ブックマーク状態に応じて初期テキスト設定 (bookmark.js 側で処理される想定だが念のため)
                    // button.textContent = isBookmarked(a.url) ? '解除' : '追加';

                    li.appendChild(link); // リンクを先に追加
                    li.appendChild(button); // ボタンを後に追加
                    ul.appendChild(li);
                });
                section.appendChild(ul);
                articleList.appendChild(section);
            });

            pageInfo.textContent = totalPages > 0 ? `ページ ${currentPage} / ${totalPages}` : '該当記事なし';
            pageInput.max = totalPages;
            pageInput.placeholder = totalPages > 0 ? `1-${totalPages}` : 'ページ'; // プレースホルダー更新
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;

            // 記事リスト生成後にブックマークボタンを更新
            updateBookmarkButtons(); // bookmark.js 内の関数を呼び出す
        }


        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderArticles();
                window.scrollTo(0, 0); // ページトップへスクロール
            }
        });

        nextPageBtn.addEventListener('click', () => {
            // totalPages の再計算が必要な場合があるため renderArticles 内で制限するのが確実
            currentPage++;
            renderArticles();
            window.scrollTo(0, 0); // ページトップへスクロール
        });

        goPageBtn.addEventListener('click', () => {
            const page = parseInt(pageInput.value);
             // totalPages を現在のフィルター状態で再計算
            const query = searchBar.value.toLowerCase();
            const selectedDate = dateFilter.value;
            const selectedPersona = personaFilter.value;
            const filteredCount = articles.filter(a => {
                 const matchesSearch = query === '' ||
                    a.title.toLowerCase().includes(query) ||
                    a.date.includes(query) ||
                    (a.personality && a.personality.toLowerCase().includes(query));
                const matchesDate = selectedDate === '' || a.date === selectedDate;
                const matchesPersona = selectedPersona === '' || a.personality === selectedPersona;
                return matchesSearch && matchesDate && matchesPersona;
            }).length;
            const totalPages = Math.ceil(filteredCount / itemsPerPage);

            if (!isNaN(page) && page >= 1 && page <= totalPages) {
                currentPage = page;
                renderArticles();
                window.scrollTo(0, 0); // ページトップへスクロール
            } else if (totalPages > 0) {
                alert(`ページ番号は1から${totalPages}の間で入力してください。`);
            } else {
                 alert(`現在表示できるページがありません。`);
            }
            pageInput.value = ''; // 入力後クリア
        });

        pageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                 e.preventDefault(); // フォーム送信を抑制
                 goPageBtn.click();
            }
        });

        searchBar.addEventListener('input', () => {
            currentPage = 1; // 検索時は1ページ目に戻る
            renderArticles();
        });

        dateFilter.addEventListener('change', () => {
            currentPage = 1; // フィルター変更時は1ページ目に戻る
            renderArticles();
        });
        personaFilter.addEventListener('change', () => {
            currentPage = 1; // フィルター変更時は1ページ目に戻る
            renderArticles();
        });
    </script>
</body>
</html>
"""
    return index_html

def update_website():
    base_dir = "content"
    public_dir = "docs"
    os.makedirs(public_dir, exist_ok=True)
    
    all_metadata = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                md_path = json_path.replace(".json", ".md")
                html_filename = file.replace(".json", ".html")
                
                rel_dir = os.path.relpath(root, base_dir)
                output_dir = os.path.join(public_dir, rel_dir)
                os.makedirs(output_dir, exist_ok=True)
                
                with open(json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    all_metadata.append(metadata)
                
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                html_content = generate_html_from_markdown(md_content, metadata)
                html_path = os.path.join(output_dir, html_filename)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
    
    # index.htmlを生成
    index_html = generate_index_page(all_metadata)
    with open(os.path.join(public_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

# JSONファイルから一番上のツイート内容を取得
def get_tweet_content(json_file="./docs/articles.json"):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 一番上の記事を取得
    tweet_data = data[0]
    title = tweet_data["title"]
    url = tweet_data["url"]
    theme=tweet_data["theme"]
    wiki_title=tweet_data["wiki_title"]
    persona=tweet_data["personality"]
    
    return f"{title}\n #{theme}\n #{wiki_title}\n {persona}風\n https://satoueiei.github.io/NewsLIEbrary/{url}"

def login_func(driver, username, password, mail, phone):
    driver.get("https://x.com/login")
    time.sleep(20)
    
    print(username)
    driver.find_element(By.XPATH, '//input[@name="text"]').send_keys(username)
    
    # 「Next」ボタン
    driver.find_element(By.XPATH, '//div/span/span[text()="Next"]').click()
    time.sleep(20)
    
    # 異常画面の処理
    try:
        # 異常画面の入力欄を仮定（name="text"が再利用されるケース）
        verification_field = driver.find_element(By.XPATH, '//input[@name="text"]')
        print("異常画面が検出されました。メールアドレスを入力します")
        verification_field.send_keys(mail)
        driver.find_element(By.XPATH, "//*[text()='Next']").click()
        time.sleep(20)
    except Exception as e:
        print(f"異常画面は出ませんでした（直接パスワード画面へ進んだと仮定）:{e}")
        time.sleep(20)
        
    password_field = driver.find_element(By.XPATH, '//input[@name="password"]')
    password_field.send_keys(password)
    
    driver.find_element(By.XPATH, '//div/span/span[text()="Log in"]').click()
    time.sleep(20)
    
    try:
        # 異常画面2の入力欄を仮定（name="text"が再利用されるケース）
        phone_field = driver.find_element(By.XPATH, '//input[@name="text"]')
        print("異常画面2が検出されました。電話番号を入力します")
        phone_field.send_keys(phone)
        driver.find_element(By.XPATH, "//*[text()='Next']").click()
        time.sleep(20)
    except Exception as e:
        print(f"異常画面2は出ませんでした（ログインしたと仮定）:{e}")
        time.sleep(20)    


def filter_bmp(text):
    #BMP外の文字（U+10000以降）を除去または置換
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

def send_post(driver, post_text):
    #1. 投稿入力欄をクラス名 'notranslate' で特定し、クリック
    element = driver.find_element(By.CLASS_NAME, 'notranslate')
    element.click()
    
    #2. post_text を入力欄に送信
    filterd_text=filter_bmp(post_text)
    element.send_keys(filterd_text)
    time.sleep(2)  # 20秒待機（入力後の処理を待つため？）

    #3. 投稿ボタンをXPathで特定し、JavaScriptでクリック
    element = driver.find_element(By.XPATH, '//*[@data-testid="tweetButtonInline"]')
    driver.execute_script("arguments[0].click();", element)

def get_post(driver, account):
    driver.get(f"https://x.com/{account}")
    posts = [element.text for element in driver.find_elements(By.CLASS_NAME, 'css-1jxf684')]
    return posts

def setup_selenium_driver():
    chrome_options = Options()
    
    # GitHub Actions環境向けの追加オプション
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # ChromeDriverManagerは不要になる
    driver = webdriver.Chrome(options=chrome_options)
    print(driver.title)  # 日本語のタイトルが表示されるはず
    return driver
async def send_tweet(content):
    client.load_cookies('cookies.json')
    await client.create_tweet(content)
    
    
async def main():
    # 既存の記事を読み込む
    articles = load_articles_json()
    sequel_candidate = find_sequel_candidate(articles, days_threshold=30)

    if sequel_candidate:
        # 続編候補が見つかった場合、確率で続編か通常記事かを選択
        if random.random() < 0.1:  # 10%の確率で続編を生成
            print(f"続編を生成します: {sequel_candidate['title']}")
            content, metadata = generate_sequel_article(sequel_candidate)
        else:
            print("続編候補が見つかりましたが、今回は通常の記事を生成します")
            content, metadata = generate_news_article()
    else:
        # 通常の記事を生成（非同期）
        print("通常の記事を生成します")
        content, metadata = await generate_news_article2()  # awaitで呼び出し

    content_path, metadata_path = save_article(content, metadata)
    print(f"記事を保存しました: {content_path}")

    update_website()

    tweet_text = get_tweet_content()
    await send_tweet(tweet_text)  # awaitで呼び出し
    print("ツイートを送信しました")

    # Selenium部分はコメントアウトされてるので、そのままにしてる
    '''
    driver = setup_selenium_driver()
    update_website()
    try:
        login_func(driver, username, password, mail, phone)
        tweet_text = get_tweet_content()
        send_post(driver, tweet_text)
        posts = get_post(driver, "namekorori2")
        print(posts)
    finally:
        driver.quit()
    '''
    print("ウェブサイトを更新しました")

if __name__ == "__main__":
    asyncio.run(main())  # 1回だけasyncio.run()
