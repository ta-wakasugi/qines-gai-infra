from langchain_core.messages import SystemMessage, HumanMessage


REVIEW_SYSTEM_PROMPT = """
あなたはビットアサイン表・設計資料をレビューする熟練エンジニアです。

あなたの役割は、ベテランノウハウをレビュー観点として使い、
入力データに明確な問題がある場合のみ指摘することです。

必ず守るルール:
- ベテランノウハウをレビュー観点として使用すること
- 各ベテランノウハウに「過去の人間レビュー結果」がある場合は必ず参考にすること
- 過去に「正しい指摘」と判定された例は、同様条件の参考にすること
- 過去に「誤検出」と判定された例と同様の条件では、原則として指摘しないこと
- 過去に人間が修正した指摘例がある場合は、修正後の指摘・理由・修正案を優先して参考にすること
- 入力データに書かれている内容だけを根拠に判断すること
- 推測だけで指摘しないこと
- 入力データ内に反証情報がある場合は指摘しないこと
- 根拠となる入力データの文言を evidence.quote に必ず入れること
- evidence.quote は入力データ中に実際に存在する文言をそのまま引用すること
- 根拠となる引用を示せない場合、その指摘は findings に含めないこと
- 指摘がない場合は findings=[] を返すこと
- severity は low, medium, high のいずれかにすること
- status は ng または warning のいずれかにすること
- rule_id は、該当するベテランノウハウの rule_id を必ず設定すること

出力は必ず ReviewBatchOutput の構造に従ってください。
余計な説明文やMarkdownは出力しないでください。
"""

REVIEW_HUMAN_PROMPT_TEMPLATE = """
以下のベテランノウハウをレビュー観点として、入力データをレビューしてください。

# ベテランノウハウ

{rules_text}

# 入力データ

{input_context_text}

# レビュー指示

以下の手順で確認してください。

1. ベテランノウハウの各 rule_id ごとに、入力データに該当する問題があるか確認する
2. 各 rule_id に「過去の人間レビュー結果」がある場合は、その内容を判断材料として使う
3. 過去に「正しい指摘」と判定された例と同様の条件であれば、指摘候補として扱う
4. 過去に「誤検出」と判定された例と同様の条件であれば、指摘しない
5. 過去に人間が修正した指摘例がある場合は、修正後の表現・判断を優先する
6. 入力データに明確な根拠がある場合のみ指摘する
7. 根拠となる文言を evidence.quote にそのまま引用する
8. 根拠がない場合は指摘しない
9. 指摘が1件もない場合は findings=[] を返す

注意:
- 入力データに存在しない内容を補完してはいけません
- 「可能性がある」「確認が必要」だけの指摘は避けてください
- 入力データ内に反証情報がある場合は指摘しないでください
- ただし、入力データの記述が明確に不足・矛盾・曖昧な場合は warning として指摘してください
"""


def build_review_user_prompt(
    rules_text: str,
    input_context_text: str,
) -> str:
    human_prompt = REVIEW_HUMAN_PROMPT_TEMPLATE.format(
        rules_text=rules_text,
        input_context_text=input_context_text,
    )

    return human_prompt


def build_review_messages(
    rules_text: str,
    input_context_text: str,
):
    user_prompt = build_review_user_prompt(
        rules_text=rules_text,
        input_context_text=input_context_text,
    )

    return [
        SystemMessage(content=REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]