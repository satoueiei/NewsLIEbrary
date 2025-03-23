import feedparser
import google.generativeai as genai
import requests
import random
import os
import json
from datetime import datetime
import markdown

# Geminiと接続
GOOGLE_API_KEY = 'AIzaSyBj93AYpuJFPG5bjfzh-miAp36qp0z10Qo'
genai.configure(api_key=GOOGLE_API_KEY)

def generate_news_article():
    # GoogleTrendsのRSSフィードを読み込む
    feed = feedparser.parse('https://trends.google.co.jp/trending/rss?geo=JP')
    titles = [entry['title'] for entry in feed['entries']]

    # Wikipediaのエンドポイントに接続
    Ses = requests.Session()
    URL = "https://ja.wikipedia.org/w/api.php"

    # パラメータ指定
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnlimit": "10",
        "rnnamespace": "0"
    }

    # リクエスト
    R = Ses.get(url=URL, params=PARAMS)
    DATA = R.json()
    RANDOMS = DATA["query"]["random"]

    # ランダムなタイトルを選択
    wiki_title = random.choice(RANDOMS)["title"]

    # Geminiモデル選択
    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")

    # プロンプト作成
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
        "エンジニア", "宇宙人", "タイムトラベラー", "恋愛マスター", "怠け者"
    ]

    theme = random.choice(titles)
    personality = random.choice(personalities)
    
    # 日付と時間を取得
    now = datetime.now()
    date_string = now.strftime("%Y年%m月%d日")
    time_string = now.strftime("%H:%M")
    
    prompt = f"架空のニュースサイト、「News LIE-brary」に載せるための、「{theme}」と「{wiki_title}」をテーマにした架空のネットニュースを作ってください。「{personality}」風な文体で、1000~2000字程度を参考に作ってください。タイトルをつけ、タイトルの初めにはニュースサイトの名前を【】で囲んで必ず記述してください。日付は {date_string} とし、記事の一番上に表示してください。なお、レスポンスはニュース記事の部分のみにしてください。"
    
    # 生成
    response = model.generate_content(prompt)
    content = response.text
    
    # 記事のメタデータを作成
    metadata = {
        "date": now.strftime("%Y-%m-%d"),
        "time": time_string,
        "theme": theme,
        "wiki_title": wiki_title,
        "personality": personality,
        "timestamp": now.timestamp()
    }
    
    return content, metadata

def save_article(content, metadata):
    # ディレクトリ構造を作成
    base_dir = "content"
    year_dir = os.path.join(base_dir, metadata["date"][:4])
    month_dir = os.path.join(year_dir, metadata["date"][5:7])
    os.makedirs(month_dir, exist_ok=True)
    
    # ファイル名を生成（タイムスタンプを使用）
    timestamp = metadata["timestamp"]
    filename_base = f"{metadata['date']}-{int(timestamp)}"
    
    # マークダウンファイルとして保存
    content_path = os.path.join(month_dir, f"{filename_base}.md")
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # メタデータをJSONとして保存
    metadata_path = os.path.join(month_dir, f"{filename_base}.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return content_path, metadata_path

def generate_html_from_markdown(md_content, metadata):
    """マークダウンからHTMLを生成"""
    html_content = markdown.markdown(md_content)
    
    # 簡単なHTMLテンプレート
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大滑子帝国広報部 - {metadata['theme']} x {metadata['wiki_title']}</title>
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{ border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; }}
        footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.8em; color: #666; }}
        .metadata {{ font-size: 0.9em; color: #666; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部</h1>
        <p>ニュースサイト「News LIE-brary」が、大滑子帝国の日常をお届けします。</p>
    </header>
    <main>
        <article>
            {html_content}
        </article>
        <div class="metadata">
            <p>テーマ: {metadata['theme']} x {metadata['wiki_title']}</p>
            <p>文体: {metadata['personality']}風</p>
            <p>生成日時: {metadata['date']} {metadata['time']}</p>
        </div>
    </main>
    <footer>
        <p>このニュースは自動生成されたフィクションです。実在の人物・団体とは関係ありません。</p>
    </footer>
</body>
</html>
"""
    return html_template

def generate_index_page(articles_metadata):
    """記事一覧ページを生成"""
    # 記事を日付順に並べ替え
    sorted_articles = sorted(articles_metadata, key=lambda x: x["timestamp"], reverse=True)
    
    article_list_html = ""
    for article in sorted_articles:
        article_date = article["date"]
        year = article_date[:4]
        month = article_date[5:7]
        filename_base = f"{article_date}-{int(article['timestamp'])}"
        
        article_list_html += f"""
        <li>
            <a href="{year}/{month}/{filename_base}.html">
                {article["theme"]} x {article["wiki_title"]} ({article["personality"]}風)
            </a>
            <span class="date">{article["date"]}</span>
        </li>
        """
    
    index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大滑子帝国広報部 - アーカイブ</title>
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{ border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; }}
        footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.8em; color: #666; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; }}
        .date {{ color: #666; font-size: 0.9em; margin-left: 10px; }}
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部 - アーカイブ</h1>
        <p>ニュースサイト「News LIE-brary」のニュース記事のアーカイブです</p>
    </header>
    <main>
        <ul>
            {article_list_html}
        </ul>
    </main>
    <footer>
        <p>このサイトのすべてのニュースは自動生成されたフィクションです。実在の人物・団体とは関係ありません。</p>
    </footer>
</body>
</html>
"""
    return index_html

def update_website():
    """ウェブサイト全体を更新"""
    base_dir = "content"
    public_dir = "docs"
    os.makedirs(public_dir, exist_ok=True)
    
    # すべての記事メタデータを収集
    all_metadata = []
    
    # ディレクトリを再帰的に検索
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                md_path = json_path.replace(".json", ".md")
                html_filename = file.replace(".json", ".html")
                
                # 相対パスを計算
                rel_dir = os.path.relpath(root, base_dir)
                output_dir = os.path.join(public_dir, rel_dir)
                os.makedirs(output_dir, exist_ok=True)
                
                # メタデータを読み込む
                with open(json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    all_metadata.append(metadata)
                
                # マークダウンを読み込む
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                # HTMLを生成して保存
                html_content = generate_html_from_markdown(md_content, metadata)
                html_path = os.path.join(output_dir, html_filename)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
    
    # インデックスページを生成
    index_html = generate_index_page(all_metadata)
    with open(os.path.join(public_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

def main():
    # 新しい記事を生成
    content, metadata = generate_news_article()
    
    # 記事を保存
    content_path, metadata_path = save_article(content, metadata)
    print(f"記事を保存しました: {content_path}")
    
    # ウェブサイトを更新
    update_website()
    print("ウェブサイトを更新しました")

if __name__ == "__main__":
    main()