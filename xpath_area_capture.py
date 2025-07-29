import sys
import time
import re
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROME_BINARY_PATH, CHROME_DRIVER_PATH, DEBUG

def normalize_xpath(xpath):
    """
    XPathの引数内のクォートを正規化する
    """
    try:
        # [@id="value"] パターンを [@id='value'] に変換
        pattern = r'(\[@[^=]+)=("([^"]+)")'
        normalized = re.sub(pattern, lambda m: f"{m.group(1)}='{m.group(3)}'", xpath)
        
        if DEBUG and normalized != xpath:
            print(f"XPathを正規化しました: {xpath} -> {normalized}")
        
        return normalized
    except Exception as e:
        if DEBUG:
            print(f"XPath正規化中にエラーが発生: {str(e)}")
        return xpath

def validate_xpath(xpath):
    """
    XPathの基本的な妥当性をチェック
    """
    if not xpath:
        raise ValueError("XPathが空です")
    
    # 基本的な構文チェック
    if not xpath.startswith(('/', './/')):
        raise ValueError("XPathは'/'または'//'で始める必要があります")
    
    # 括弧の対応チェック
    if xpath.count('[') != xpath.count(']'):
        raise ValueError("XPathの括弧[]の対応が取れていません")
    
    try:
        # 正規化を試行して構文の妥当性を確認
        normalized = normalize_xpath(xpath)
        if not normalized:
            raise ValueError("XPathの正規化に失敗しました")
    except Exception as e:
        raise ValueError(f"XPathの構文が不正です: {str(e)}")

def setup_chrome_driver():
    """
    ChromeDriverの設定を行い、インスタンスを返す
    """
    options = Options()
    options.binary_location = CHROME_BINARY_PATH
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--enable-logging')
    options.add_argument('--log-level=1')
    options.add_argument('--force-device-scale-factor=1')
    options.add_argument('--window-size=1920,1080')

    service = Service(executable_path=CHROME_DRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def wait_for_page_load(driver):
    """
    ページの読み込みが完了するまで待機
    """
    def page_has_loaded(driver):
        return driver.execute_script("return document.readyState") == "complete"

    WebDriverWait(driver, 30).until(page_has_loaded)
    time.sleep(5)  # 追加の待機時間

def scroll_and_wait_for_content(driver, target_xpath, max_attempts=3):
    """
    段階的にスクロールしながら要素を探索
    """
    if DEBUG:
        print(f"段階的スクロール戦略を開始: {target_xpath}")
    
    # 1. 通常の待機で要素を探索
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, target_xpath))
        )
        if DEBUG:
            print("通常の待機で要素が見つかりました")
        return element
    except Exception as e:
        if DEBUG:
            print(f"通常の待機では要素が見つかりませんでした: {str(e)}")
    
    # 2. ページ全体をスクロールしながら探索
    for attempt in range(max_attempts):
        if DEBUG:
            print(f"スクロール試行 {attempt + 1}/{max_attempts}")
        
        # 段階的にスクロール
        scroll_positions = [0.25, 0.5, 0.75, 1.0]  # ページの25%ずつスクロール
        
        for position in scroll_positions:
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
            time.sleep(2)  # スクロール後の待機
            
            if DEBUG:
                print(f"スクロール位置: {int(position * 100)}%")
            
            # 要素の存在を確認
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, target_xpath))
                )
                if DEBUG:
                    print(f"スクロール位置 {int(position * 100)}% で要素が見つかりました")
                return element
            except:
                continue
        
        # 最下部で少し長めに待機
        if DEBUG:
            print("最下部で追加待機中...")
        time.sleep(5)
        
        # 最下部での最終確認
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, target_xpath))
            )
            if DEBUG:
                print("最下部での最終確認で要素が見つかりました")
            return element
        except:
            # 上部に戻ってから再度試行
            if DEBUG:
                print("上部に戻って再試行します")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
    
    raise ValueError(f"スクロール後も要素が見つかりません: {target_xpath}")

def advanced_content_loading_strategy(driver, target_xpath):
    """
    高度な動的コンテンツ読み込み戦略
    """
    if DEBUG:
        print("高度な動的コンテンツ読み込み戦略を開始")
    
    # Step 1: 基本的な待機
    wait_for_page_load(driver)
    
    # Step 2: ネットワークアクティビティの監視を設定
    driver.execute_script("""
        window.networkIdle = false;
        window.requestCount = 0;
        window.loadingComplete = false;
        
        // XMLHttpRequest の監視
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            const originalSend = xhr.send;
            
            xhr.open = function(...args) {
                window.requestCount++;
                return originalOpen.apply(this, args);
            };
            
            xhr.addEventListener('loadend', function() {
                window.requestCount--;
                if (window.requestCount <= 0) {
                    setTimeout(() => {
                        window.networkIdle = true;
                        window.loadingComplete = true;
                    }, 1000);
                }
            });
            
            return xhr;
        };
        
        // Fetch API の監視
        if (window.fetch) {
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                window.requestCount++;
                return originalFetch.apply(this, args).finally(() => {
                    window.requestCount--;
                    if (window.requestCount <= 0) {
                        setTimeout(() => {
                            window.networkIdle = true;
                            window.loadingComplete = true;
                        }, 1000);
                    }
                });
            };
        }
        
        // 初期状態を設定
        setTimeout(() => {
            if (window.requestCount <= 0) {
                window.networkIdle = true;
                window.loadingComplete = true;
            }
        }, 3000);
    """)
    
    # Step 3: スクロールによるコンテンツ読み込み
    try:
        return scroll_and_wait_for_content(driver, target_xpath)
    except ValueError:
        if DEBUG:
            print("スクロール戦略が失敗、ネットワークアイドル待機を試行")
    
    # Step 4: ネットワークアイドル状態の待機
    try:
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return window.loadingComplete === true")
        )
        if DEBUG:
            print("ネットワークアイドル状態を確認")
    except Exception as e:
        if DEBUG:
            print(f"ネットワークアイドル待機がタイムアウト: {str(e)}")
    
    # 最終的な要素探索
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, target_xpath))
        )
        if DEBUG:
            print("最終的な要素探索で要素が見つかりました")
        return element
    except Exception as e:
        if DEBUG:
            print(f"最終的な要素探索も失敗: {str(e)}")
        raise ValueError(f"全ての戦略を試行しても要素が見つかりません: {target_xpath}")

def get_element_by_xpath(driver, xpath):
    """
    XPathで要素を取得し、その要素が画像の場合はsrcの値も確認
    動的コンテンツ対応戦略を使用
    """
    # 高度な動的コンテンツ読み込み戦略を使用
    element = advanced_content_loading_strategy(driver, xpath)
    
    # 要素の表示を待機
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
    except Exception as e:
        if DEBUG:
            print(f"要素の表示待機でタイムアウト: {str(e)}")
        # 要素が存在するが非表示の場合もあるので、処理を続行
    
    # img要素の場合、画像の読み込みを待機
    if element.tag_name == 'img':
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script(
                    "return arguments[0].complete && typeof arguments[0].naturalWidth != 'undefined' && arguments[0].naturalWidth > 0",
                    element
                )
            )
        except Exception as e:
            if DEBUG:
                print(f"画像読み込み待機でタイムアウト: {str(e)}")
        
        if DEBUG:
            src = element.get_attribute('src')
            print(f"画像のsrc: {src}")
    
    return element

def capture_element_area(url, xpath, output_path):
    """
    指定されたXPathの要素の範囲のみをキャプチャ
    """
    driver = setup_chrome_driver()
    
    try:
        # ページにアクセス
        print(f"ページにアクセス中: {url}")
        driver.get(url)
        
        # ページの読み込みを待機
        print("ページの読み込みを待機中...")
        wait_for_page_load(driver)
        
        # 要素を探索
        print(f"要素を探索中: {xpath}")
        
        # ページのHTMLソースを取得して確認
        if DEBUG:
            print("ページのHTMLソースを確認中...")
            page_source = driver.page_source
            print(f"ページのHTMLソースの長さ: {len(page_source)} 文字")
            
            # 特定のIDを持つ要素を探す
            if "main-image" in page_source:
                print("'main-image' IDがページ内に存在します")
            else:
                print("警告: 'main-image' IDがページ内に存在しません")
            
            # ページ内のすべての画像要素を出力
            print("ページ内の画像要素を探索中...")
            images = driver.find_elements(By.TAG_NAME, "img")
            print(f"ページ内の画像要素数: {len(images)}")
            for i, img in enumerate(images):
                img_id = img.get_attribute('id')
                img_src = img.get_attribute('src')
                img_alt = img.get_attribute('alt')
                img_class = img.get_attribute('class')
                print(f"画像 {i+1}: id='{img_id}', class='{img_class}', src='{img_src}', alt='{img_alt}'")
                
                # 最初の5つの画像のみ表示（多すぎる場合）
                if i >= 4 and len(images) > 5:
                    print(f"... 他 {len(images) - 5} 個の画像があります")
                    break
        
        # 元のXPathで要素を探索
        try:
            element = get_element_by_xpath(driver, xpath)
            print(f"指定されたXPath '{xpath}' で要素が見つかりました")
        except Exception as e:
            print(f"指定されたXPath '{xpath}' での要素探索に失敗しました")
            
            # ページ内に画像要素が存在するか確認
            images = driver.find_elements(By.TAG_NAME, "img")
            if not images:
                print("エラー: ページ内に画像要素が見つかりません")
                raise ValueError("ページ内に画像要素が見つかりません。XPathを確認してください。")
            
            print("\nエラー: 指定されたXPathの要素が見つかりませんでした。")
            print("ページの構造を確認して、正しいXPathを指定してください。")
            raise ValueError(f"XPath '{xpath}' の要素が見つかりませんでした。")
        
        # 要素が表示されるようにスクロール（中央配置）
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(3)  # スクロールのアニメーションを待機
        
        # ヘッダーとフッターを非表示にする
        print("ヘッダーとフッターを非表示にしています...")
        result = driver.execute_script("""
            // ヘッダー要素を非表示
            var headers = document.getElementsByTagName('header');
            for (var i = 0; i < headers.length; i++) {
                headers[i].style.display = 'none';
            }
            
            // フッター要素を非表示
            var footers = document.getElementsByTagName('footer');
            for (var i = 0; i < footers.length; i++) {
                footers[i].style.display = 'none';
            }
            
            return {
                headerCount: headers.length,
                footerCount: footers.length
            };
        """)
        
        if DEBUG:
            print(f"非表示にした要素: ヘッダー {result['headerCount']}個, フッター {result['footerCount']}個")
        
        # 変更が反映されるまで少し待機
        time.sleep(1)
        
        # JavaScriptで要素の情報を取得
        info = driver.execute_script("""
            var element = arguments[0];
            var rect = element.getBoundingClientRect();
            var style = window.getComputedStyle(element);
            return {
                tagName: element.tagName.toLowerCase(),
                src: element.src || null,
                x: rect.left,
                y: rect.top + window.pageYOffset,
                width: rect.width,
                height: rect.height,
                display: style.display,
                visibility: style.visibility
            };
        """, element)
        
        if DEBUG:
            print(f"要素の情報: {info}")
        
        if info['display'] == 'none' or info['visibility'] == 'hidden':
            raise ValueError("要素が非表示です")
        
        # 要素のスクリーンショットを直接取得
        print("スクリーンショットを撮影中...")
        element_png = element.screenshot_as_png
        
        # 画像として保存
        with open(output_path, 'wb') as f:
            f.write(element_png)
        
        print(f"スクリーンショットを保存しました: {output_path}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        if DEBUG:
            import traceback
            print("詳細なエラー情報:")
            print(traceback.format_exc())
        sys.exit(1)
    finally:
        driver.quit()

def main():
    if len(sys.argv) != 4:
        print("使用方法: python xpath_area_capture.py URL XPath 出力ファイル名")
        print("例: python xpath_area_capture.py https://example.com '//div[@id=\"main\"]' output.png")
        sys.exit(1)

    url = sys.argv[1]
    xpath = sys.argv[2]
    output_path = sys.argv[3]

    try:
        # XPathの妥当性チェック
        try:
            validate_xpath(xpath)
        except ValueError as e:
            print(f"XPathエラー: {e}")
            sys.exit(1)

        # XPathの正規化
        xpath = normalize_xpath(xpath)

        capture_element_area(url, xpath, output_path)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        if DEBUG:
            import traceback
            print("詳細なエラー情報:")
            print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()