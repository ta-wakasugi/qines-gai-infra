from dotenv import load_dotenv

from qines_gai_backend.logger_config import get_logger, log_function_start_end
from qines_gai_backend.modules.ai.llm_wrapper import LLMWrapper
from qines_gai_backend.modules.artifacts.models import PowerPoint

load_dotenv("/app/.env")
logger = get_logger(__name__)


@log_function_start_end
def markdown_to_powerpoint(markdown_input: str) -> PowerPoint:
    """LLMを利用してMarkdownをPowerPointオブジェクトに変換します。

    Args:
        markdown_input: 変換対象のMarkdown文字列。

    Returns:
        生成されたPowerPointオブジェクト。
        このオブジェクトは、タイトルとPageオブジェクト（TextPageまたはTablePage）のリストを含みます。
    """

    prompt = f"""
# 以下のマークダウンをPowerPointプレゼンテーションの構造に変換してください。

## 注意点：

* マークダウンのすべてのコンテンツをPowerPointに反映してください。
* マークダウンの構造をそのまま利用する必要はありません。
* マークダウンのコンテンツを、PowerPointの各スライドが見やすく理解しやすい情報量になるように分割してください。
* 1つのスライドに詰め込みすぎず、適切な量の情報になるように調整してください。
* スライドの情報を確認して、適切なスライドオブジェクトを選択してください。
* 基本的にはTextPageオブジェクトを使用してください。
* マークダウンに表がある場合、または、テキストより表形式の方が分かりやすい場合は、TablePageオブジェクトを利用してください。
* 1行('TextSection'オブジェクトの'content'フィールド)に内容を詰め込みすぎず、適切な量の情報になるように調整してください。
* 'TextPage'オブジェクトの'sections'フィールドは、少なくとも1つの要素を含むリストにしてください。
* 'TextSection'オブジェクトの'content'フィールドは、少なくとも1つの要素を含むリストにしてください。
* 1セル('TablePage'オブジェクトの'table_data'フィールド)に内容を詰め込みすぎず、適切な量の情報になるように調整してください。
* 'TextSection'オブジェクトの'table_data'フィールドは、少なくとも2つの要素を含むリストにしてください。

## マークダウン：
{markdown_input}

## PowerPointオブジェクト作成例
```python
PowerPoint(
    title="PythonとJavaScript：人気のプログラミング言語",
    pages=[
        TablePage(
            header="Python vs JavaScript",
            content="PythonとJavaScriptの比較",
            template="table",
            policy="表形式で比較を分かりやすく示す",
            table_section=TableSection(
                title="",
                table_data=[
                    ["項目", "Python", "JavaScript"],
                    ["特徴", "シンプルで読みやすい文法、オープンソースで無料利用可能、豊富なライブラリとフレームワーク、コミュニティサポートによる継続的な改善・更新", "動的なウェブサイト構築、柔軟な文法、豊富なライブラリ、Node.jsによるサーバーサイド開発、非同期処理、フロントエンドフレームワークとの連携"],
                    ["文法", "インデントベース", "プロトタイプベースのオブジェクト指向"],
                    ["ライブラリ/フレームワーク", "NumPy, Pandas, Scikit-learn, TensorFlow, PyTorch, Django, Flask 等", "jQuery, React, Vue.js, Angular, Node.js 等"],
                    ["主な用途", "データサイエンス、機械学習、Web開発、自動化スクリプト", "Webフロントエンド開発、Webバックエンド開発 (Node.js)、モバイルアプリ開発 (React Native, Ionicなど)、デスクトップアプリ開発 (Electronなど)"],
                    ["メリット", "初心者にも学習しやすい、可読性が高い、開発効率が高い、多様な分野への応用が可能", "Web開発に不可欠、フロントエンドとバックエンドで同じ言語を使用可能、非同期処理に強い、豊富なフロントエンドフレームワーク"],
                ],
            ),
        ),
        TextPage(
            header="Pythonの詳細",
            content="Pythonはシンプルで読みやすい文法が特徴です。初心者にも学習しやすく、様々な分野で活用されています。",
            template="text",
            policy="Pythonの特徴を詳細に説明し、利点を分かりやすく伝える",
            sections=[
                TextSection(
                    title="シンプルで読みやすい文法",
                    content=[
                        "インデントベースの構文によりコード構造が明確",
                        "初心者にも理解しやすい",
                        "可読性が高い",
                    ],
                ),
                TextSection(
                    title="豊富なライブラリとフレームワーク",
                    content=[
                        "NumPy, Pandas, Scikit-learn (データサイエンス)",
                        "TensorFlow, PyTorch (機械学習)",
                        "Django, Flask (Web開発)",
                    ],
                ),
                TextSection(
                    title="多様な応用分野", content=["データサイエンス", "機械学習", "Web開発", "自動化スクリプト"]),
            ],
        ),
        TextPage(
            header="JavaScriptの詳細",
            content="JavaScriptはWeb開発の中核を担う言語です。近年はサーバーサイドやモバイルアプリ開発にも活用されています。",
            template="text",
            policy="JavaScriptの進化と多様な用途を説明する",
            sections=[
                TextSection(
                    title="Webフロントエンド開発",
                    content=["動的なウェブサイト構築", "インタラクティブな要素の実装"],
                ),
                TextSection(
                    title="Webバックエンド開発 (Node.js)",
                    content=["サーバーサイドJavaScriptの実行環境", "フロントエンドとバックエンドで同じ言語を使用可能"],
                ),
                TextSection(
                    title="モバイルアプリ開発",
                    content=["React Native, Ionicなど"],
                ),
                 TextSection(
                    title="デスクトップアプリ開発",
                    content=["Electronなど"],
                ),
            ],
        ),
        TextPage(
            header="まとめ",
            content="PythonとJavaScriptはそれぞれ異なる特徴を持つ強力な言語です。",
            template="text",
            policy="PythonとJavaScriptのそれぞれの利点を改めて強調する",
            sections=[
                TextSection(
                    title="Pythonの利点",
                    content=["データサイエンス、機械学習に最適", "シンプルで学習しやすい"],
                ),
                TextSection(
                    title="JavaScriptの利点",
                    content=["Web開発の中核", "フロントエンドとバックエンドで同じ言語を使用可能"],
                ),
            ],
        ),
    ],
)
```

## PowerPointオブジェクト作成
"""
    wrapper = LLMWrapper()

    structured_llm = wrapper.get_structured_llm(PowerPoint, temperature=0)

    result = structured_llm.invoke(prompt)

    return result
