# xpath-area-capture

## Overview
A tool to capture screenshots of web elements specified by XPath. It allows you to take precise screenshots of specific elements on a webpage, ensuring accurate capture of the target element.

## Installation
1. Clone the repository
```bash
git clone https://github.com/daishir0/xpath-area-capture
cd xpath-area-capture
```

2. Create and activate a Python virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # For Linux/Mac
# or
.\venv\Scripts\activate  # For Windows
```

3. Install required packages
```bash
pip install -r requirements.txt
```

4. Configure Chrome settings
Edit `config.py` and set the correct paths for your environment:
```python
CHROME_BINARY_PATH = "/path/to/chrome"
CHROME_DRIVER_PATH = "/path/to/chromedriver"
```

## Usage
Run the program with the following command:
```bash
python xpath_area_capture.py URL XPATH OUTPUT_FILE
```

Example:
```bash
python xpath_area_capture.py "https://example.com" "//img[@id='main-image']" "output.png"
```

Parameters:
- `URL`: The webpage URL containing the target element
- `XPATH`: XPath expression to locate the target element
- `OUTPUT_FILE`: Output filename for the screenshot (PNG format)

## Notes
- Requires Google Chrome and ChromeDriver
- The program waits for the page and target element to load completely
- For image elements, it ensures the image is fully loaded before capturing
- Debug mode can be enabled in config.py to show detailed information

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# xpath-area-capture

## 概要
XPathで指定したWeb要素のスクリーンショットを取得するツールです。Webページ上の特定の要素を正確にキャプチャすることができます。

## インストール方法
1. リポジトリをクローン
```bash
git clone https://github.com/daishir0/xpath-area-capture
cd xpath-area-capture
```

2. Python仮想環境の作成と有効化（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac の場合
# または
.\venv\Scripts\activate  # Windows の場合
```

3. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

4. Chrome設定の構成
`config.py`を編集し、環境に合わせて正しいパスを設定：
```python
CHROME_BINARY_PATH = "/path/to/chrome"
CHROME_DRIVER_PATH = "/path/to/chromedriver"
```

## 使い方
以下のコマンドでプログラムを実行：
```bash
python xpath_area_capture.py URL XPATH 出力ファイル
```

例：
```bash
python xpath_area_capture.py "https://example.com" "//img[@id='main-image']" "output.png"
```

パラメータ：
- `URL`: 対象要素を含むWebページのURL
- `XPATH`: 対象要素を特定するためのXPath式
- `出力ファイル`: スクリーンショットの出力ファイル名（PNG形式）

## 注意点
- Google ChromeとChromeDriverが必要です
- ページと対象要素の完全な読み込みを待機します
- 画像要素の場合、画像が完全に読み込まれるまで待機します
- config.pyでデバッグモードを有効にすると詳細な情報が表示されます

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。