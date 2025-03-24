// ブックマークを管理する配列（ローカルストレージから取得）
let bookmarks = JSON.parse(localStorage.getItem('bookmarks')) || [];

// ブックマークの追加・削除を切り替える関数
function toggleBookmark(title, url, date, button) {
    const index = bookmarks.findIndex(b => b.url === url);
    
    if (index === -1) {
        // ブックマークに追加
        bookmarks.push({ title, url, date });
        button.textContent = 'ブクマ解除';
        button.classList.add('bookmarked');
    } else {
        // ブックマークから削除
        bookmarks.splice(index, 1);
        button.textContent = 'ブクマする';
        button.classList.remove('bookmarked');
    }
    
    saveBookmarks();
}

// ブックマークをローカルストレージに保存
function saveBookmarks() {
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
}

// ボタンの状態を記事ごとに更新
function updateBookmarkButtons() {
    document.querySelectorAll('.bookmark-btn').forEach(button => {
        const title = button.getAttribute('data-title');
        const url = button.getAttribute('data-url');
        const date = button.getAttribute('data-date');

        if (bookmarks.some(b => b.url === url)) {
            button.textContent = 'ブクマ解除';
            button.classList.add('bookmarked');
        } else {
            button.textContent = 'ブクマする';
            button.classList.remove('bookmarked');
        }

        // クリックイベントを削除してから再設定
        button.replaceWith(button.cloneNode(true)); // クリックイベントの重複を防ぐ
        const newButton = document.querySelector(`[data-url="${url}"]`);
        newButton.addEventListener('click', function() {
            toggleBookmark(title, url, date, newButton);
        });
    });
}

// 記事リストの描画後にボタンを更新
document.addEventListener('DOMContentLoaded', updateBookmarkButtons);

// ブックマークを表示する関数（bookmarks.html用）
function displayBookmarks() {
    const bookmarkList = document.getElementById('bookmark-list');
    if (!bookmarkList) return; // bookmarks.html以外では実行しない

    bookmarkList.innerHTML = '';
    bookmarks.forEach((bookmark, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>
                <a href="${bookmark.url}">${bookmark.title}</a>
                <span class="date">${bookmark.date}</span>
            </div>
            <button class="remove-btn" data-index="${index}">削除</button>
        `;
        bookmarkList.appendChild(li);
    });
}

// ブックマーク削除機能（bookmarks.html用）
function setupBookmarkRemoval() {
    const bookmarkList = document.getElementById('bookmark-list');
    if (!bookmarkList) return; // bookmarks.html以外では実行しない

    bookmarkList.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-btn')) {
            const index = e.target.getAttribute('data-index');
            bookmarks.splice(index, 1); // 配列から削除
            saveBookmarks(); // 保存
            displayBookmarks(); // 再表示
        }
    });
}

// ページ読み込み時にブックマークを表示（bookmarks.html用）
if (document.getElementById('bookmark-list')) {
    displayBookmarks();
    setupBookmarkRemoval();
}
