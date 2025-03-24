import feedparser
import google.generativeai as genai
import requests
import random
import os
import json
from datetime import datetime
import markdown
import re

# Geminiと接続
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

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
        "淫夢厨"
    ]

    theme = random.choice(titles)
    personality = random.choice(personalities)
    
    now = datetime.now()
    date_string = now.strftime("%Y年%m月%d日")
    time_string = now.strftime("%H:%M")
    
    prompt = f"架空のニュースサイト、「News LIE-brary」に載せるための、「{theme}」と「{wiki_title}」をテーマにした架空のネットニュースをマークダウン形式で作ってください。「{personality}」風な文体で、1000~2000字程度を参考に作ってください。タイトルをつけ、タイトルにはニュースサイトの名前を【】で囲んで、h1として必ず記述してください。日付は {date_string} とし、記事の一番上に表示してください。ただし、ニュースサイトのほかの部分でこれが架空であることを示しますので、記事本文にはこれが架空であることを示す内容は入れないことと、回答はニュース記事部分だけにしてください。"
    
    response = model.generate_content(prompt)
    content = response.text
    
    title_match = re.search(r"^\s*#+\s*【News LIE-brary】[^\n]+", content, re.MULTILINE)
    article_title = title_match.group(0).replace("#", "").strip() if title_match else "無題の記事"
    
    metadata = {
        "date": now.strftime("%Y-%m-%d"),
        "time": time_string,
        "theme": theme,
        "wiki_title": wiki_title,
        "personality": personality,
        "timestamp": now.timestamp(),
        "title": article_title
    }
    
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
        <p class="archive-link"><a href="../../index.html">アーカイブに戻る</a></p>
    </footer>
</body>
</html>
"""
    return html_template

def generate_index_page(articles_metadata):
    sorted_articles = sorted(articles_metadata, key=lambda x: x["timestamp"], reverse=True)
    
    # 日付ごとに記事をグループ化
    articles_by_date = {}
    for article in sorted_articles:
        date = article["date"]
        if date not in articles_by_date:
            articles_by_date[date] = []
        articles_by_date[date].append(article)
    
    # 日付リストをドロップダウン用に生成（新しい順）
    date_options = '<option value="">すべての日付</option>\n'
    for date in sorted(articles_by_date.keys(), reverse=True):
        date_options += f'<option value="{date}">{date}</option>\n'
    
    # 記事リストを新しい日付順に生成
    article_list_html = ""
    for date in sorted(articles_by_date.keys(), reverse=True):
        articles = articles_by_date[date]
        article_list_html += f'<div class="date-section" data-date="{date}"><h2>{date}</h2>\n<ul>\n'
        for article in articles:
            article_date = article["date"]
            year = article_date[:4]
            month = article_date[5:7]
            filename_base = f"{article_date}-{int(article['timestamp'])}"
            article_title = article.get('title', '無題の記事')
            article_list_html += f"""
            <li class="article-item" data-title="{article_title}" data-date="{article_date}" data-personality="{article['personality']}">
                <a href="{year}/{month}/{filename_base}.html">
                    {article_title} ({article['personality']}風)
                </a>
                <span class="date">{article_date}</span>
            </li>
            """
        article_list_html += "</ul></div>\n"
    
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
        #search-bar {{ width: 70%; padding: 10px; margin-bottom: 10px; font-size: 1em; }}
        #date-filter {{ width: 25%; padding: 10px; margin-bottom: 10px; font-size: 1em; margin-left: 5px; }}
        h2 {{ color: #333; margin-top: 20px; }}
        .hidden {{ display: none; }}
        .filter-container {{ display: flex; align-items: center; gap: 10px; }}
        .pagination {{ margin-top: 20px; text-align: center; }}
        .pagination button {{ padding: 5px 10px; margin: 0 5px; cursor: pointer; }}
        .pagination button:disabled {{ cursor: not-allowed; opacity: 0.5; }}
        #page-select {{ padding: 5px; margin: 0 10px; }}
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部 - アーカイブ</h1>
        <p>ニュースサイト「News LIE-brary」のニュース記事のアーカイブです</p>
    </header>
    <main>
        <div class="filter-container">
            <input type="text" id="search-bar" placeholder="記事を検索...">
            <select id="date-filter">
                {date_options}
            </select>
        </div>
        <div id="article-list">
            {article_list_html}
        </div>
        <div class="pagination">
            <button id="prev-page" disabled>前へ</button>
            <select id="page-select"></select>
            <button id="next-page">次へ</button>
        </div>
    </main>
    <footer>
        <p>このサイトのすべてのニュースは自動生成されたフィクションです。実在の人物・団体とは関係ありません。</p>
    </footer>
    <script>
        const searchBar = document.getElementById('search-bar');
        const dateFilter = document.getElementById('date-filter');
        const articleItems = document.querySelectorAll('.article-item');
        const dateSections = document.querySelectorAll('.date-section');
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        const pageSelect = document.getElementById('page-select');
        
        const itemsPerPage = 10; // 1ページあたりの表示件数
        let currentPage = 1;
        
        function filterArticles() {{
            const query = searchBar.value.toLowerCase();
            const selectedDate = dateFilter.value;
            let visibleItems = [];
            
            dateSections.forEach(section => {{
                const sectionDate = section.getAttribute('data-date');
                let hasVisibleItems = false;
                
                section.querySelectorAll('.article-item').forEach(item => {{
                    const title = item.getAttribute('data-title').toLowerCase();
                    const date = item.getAttribute('data-date');
                    const personality = item.getAttribute('data-personality').toLowerCase();
                    
                    const matchesSearch = query === '' || 
                        title.includes(query) || 
                        date.includes(query) || 
                        personality.includes(query);
                    const matchesDate = selectedDate === '' || date === selectedDate;
                    
                    if (matchesSearch && matchesDate) {{
                        item.classList.remove('hidden');
                        visibleItems.push(item);
                        hasVisibleItems = true;
                    }} else {{
                        item.classList.add('hidden');
                    }}
                }});
                
                section.classList.toggle('hidden', !hasVisibleItems);
            }});
            
            return visibleItems;
        }}
        
        function updatePagination() {{
            const visibleItems = filterArticles();
            const totalItems = visibleItems.length;
            const totalPages = Math.ceil(totalItems / itemsPerPage);
            
            // 現在のページのアイテムを表示
            visibleItems.forEach((item, index) => {{
                const itemPage = Math.floor(index / itemsPerPage) + 1;
                item.classList.toggle('hidden', itemPage !== currentPage);
            }});
            
            // ページ選択ドロップダウンを更新
            pageSelect.innerHTML = '';
            for (let i = 1; i <= totalPages; i++) {{
                const option = document.createElement('option');
                option.value = i;
                option.textContent = 'ページ ' + i + ' / ' + totalPages;
                if (i === currentPage) option.selected = true;
                pageSelect.appendChild(option);
            }}
            
            // ボタンの状態を更新
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
            pageSelect.disabled = totalPages <= 1;
            
            // セクションの表示を調整
            dateSections.forEach(section => {{
                const hasVisibleItems = Array.from(section.querySelectorAll('.article-item'))
                    .some(item => !item.classList.contains('hidden'));
                section.classList.toggle('hidden', !hasVisibleItems);
            }});
        }}
        
        prevPageBtn.addEventListener('click', () => {{
            if (currentPage > 1) {{
                currentPage--;
                updatePagination();
            }}
        }});
        
        nextPageBtn.addEventListener('click', () => {{
            const totalItems = filterArticles().length;
            const totalPages = Math.ceil(totalItems / itemsPerPage);
            if (currentPage < totalPages) {{
                currentPage++;
                updatePagination();
            }}
        }});
        
        pageSelect.addEventListener('change', () => {{
            currentPage = parseInt(pageSelect.value);
            updatePagination();
        }});
        
        searchBar.addEventListener('input', () => {{
            currentPage = 1; // 検索時にページをリセット
            updatePagination();
        }});
        
        dateFilter.addEventListener('change', () => {{
            currentPage = 1; // 日付フィルタ時にページをリセット
            updatePagination();
        }});
        
        // 初回読み込み時にページネーションを適用
        updatePagination();
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
    
    index_html = generate_index_page(all_metadata)
    with open(os.path.join(public_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

def main():
    content, metadata = generate_news_article()
    
    content_path, metadata_path = save_article(content, metadata)
    print(f"記事を保存しました: {content_path}")
    
    update_website()
    print("ウェブサイトを更新しました")

if __name__ == "__main__":
    main()