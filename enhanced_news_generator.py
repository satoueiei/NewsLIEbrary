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
        <p class="archive-link"><a href="../../index.html">アーカイブに戻る</a></p>
        
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
            "timestamp": article["timestamp"]
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
        .filter-container { display: flex; gap: 5px; margin-bottom: 10px; }
        #search-bar { width: 70%; padding: 5px; font-size: 0.9em; }
        #date-filter { width: 30%; padding: 5px; font-size: 0.9em; }
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
        }
        .bookmark-btn.bookmarked{ 
            background: #af4c4c; 
            color: white; 
            border: none; 
            padding: 2px 5px; 
            cursor: pointer; 
            font-size: 0.8em; 
            border-radius: 2px; 
        }
        .bookmark-btn:hover { background: #45a049; }
        .bookmark-btn.bookmarked:hover { background: #a04545; }
        a { text-decoration: none; color: #0066cc; word-wrap: break-word; max-width: 80%; } /* タイトル折り返し */
        a:hover { text-decoration: underline; }
        .hidden { display: none; }
        h2 { margin: 10px 0 5px; font-size: 1.2em; color: #333; } /* 日付見出し */
    </style>
</head>
<body>
    <header>
        <h1>大滑子帝国広報部</h1>
        <p>「News LIE-brary」のアーカイブ</p>
        <p><a href="./bookmark.html">ブックマーク</a></p>
    </header>
    <main>
        <div class="filter-container">
            <input type="text" id="search-bar" placeholder="検索...">
            <select id="date-filter"><option value="">全日付</option></select>
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
        const articleList = document.getElementById('article-list');
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');
        const pageInput = document.getElementById('page-input');
        const goPageBtn = document.getElementById('go-page');
        
        const itemsPerPage = 10;
        let currentPage = 1;
        let articles = [];
        
        fetch('./articles.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTPエラー: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                articles = data;
                populateDateFilter();
                renderArticles();
            })
            .catch(error => {
                console.error('JSON読み込みエラー:', error);
                articleList.innerHTML = '<p>記事データを読み込めませんでした。</p>';
            });
        
        function populateDateFilter() {
            const dates = [...new Set(articles.map(a => a.date))].sort().reverse();
            dates.forEach(date => {
                const option = document.createElement('option');
                option.value = date;
                option.textContent = date;
                dateFilter.appendChild(option);
            });
        }
        
        function renderArticles() {
            const query = searchBar.value.toLowerCase();
            const selectedDate = dateFilter.value;

            const filteredArticles = articles.filter(a => {
                const matchesSearch = query === '' || 
                    a.title.toLowerCase().includes(query) || 
                    a.date.includes(query) || 
                    a.personality.toLowerCase().includes(query);
                const matchesDate = selectedDate === '' || a.date === selectedDate;
                return matchesSearch && matchesDate;
            });

            const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            const paginatedArticles = filteredArticles.slice(start, end);

            const articlesByDate = {};
            paginatedArticles.forEach(a => {
                if (!articlesByDate[a.date]) articlesByDate[a.date] = [];
                articlesByDate[a.date].push(a);
            });

            articleList.innerHTML = '';
            Object.keys(articlesByDate).sort().reverse().forEach(date => {
                const section = document.createElement('div');
                section.innerHTML = `<h2>${date}</h2>`;
                const ul = document.createElement('ul');
                articlesByDate[date].forEach(a => {
                    const li = document.createElement('li');

                    // ボタン要素を作成
                    const button = document.createElement('button');
                    button.classList.add('bookmark-btn');
                    button.setAttribute('data-title', a.title);
                    button.setAttribute('data-url', a.url);
                    button.setAttribute('data-date', a.date);

                    li.innerHTML = `
                        <a href="${a.url}" title="${a.title} (${a.personality}風, ${a.date})">
                            ${a.title}
                        </a>
                    `;

                    // ボタンをリストに追加
                    li.appendChild(button);
                    ul.appendChild(li);
                });
                section.appendChild(ul);
                articleList.appendChild(section);
            });

            pageInfo.textContent = totalPages > 0 ? `ページ ${currentPage} / ${totalPages}` : '記事なし';
            pageInput.max = totalPages;
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;

            // ★ 記事リスト生成後にブックマークボタンを更新
            updateBookmarkButtons();
        }

        
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderArticles();
            }
        });
        
        nextPageBtn.addEventListener('click', () => {
            currentPage++;
            renderArticles();
        });
        
        goPageBtn.addEventListener('click', () => {
            const page = parseInt(pageInput.value);
            const totalPages = Math.ceil(articles.filter(a => 
                (dateFilter.value === '' || a.date === dateFilter.value) &&
                (searchBar.value === '' || a.title.toLowerCase().includes(searchBar.value.toLowerCase()) || 
                 a.date.includes(searchBar.value) || a.personality.toLowerCase().includes(searchBar.value.toLowerCase()))
            ).length / itemsPerPage);
            if (page >= 1 && page <= totalPages) {
                currentPage = page;
                renderArticles();
            }
            pageInput.value = ''; // 入力後クリア
        });
        
        pageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') goPageBtn.click();
        });
        
        searchBar.addEventListener('input', () => {
            currentPage = 1;
            renderArticles();
        });
        
        dateFilter.addEventListener('change', () => {
            currentPage = 1;
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

def main():
    content, metadata = generate_news_article()
    
    content_path, metadata_path = save_article(content, metadata)
    print(f"記事を保存しました: {content_path}")
    
    update_website()
    print("ウェブサイトを更新しました")

if __name__ == "__main__":
    main()