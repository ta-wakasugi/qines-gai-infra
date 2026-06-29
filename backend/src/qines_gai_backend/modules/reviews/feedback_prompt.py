from qines_gai_backend.schemas.schema import ReviewResult


def format_feedback_examples_for_prompt(
    feedback_examples: list[ReviewResult],
) -> str:
    if not feedback_examples:
        return "過去の人間レビュー結果はありません。"

    correct_examples: list[ReviewResult] = []
    false_positive_examples: list[ReviewResult] = []
    fixed_examples: list[ReviewResult] = []

    for example in feedback_examples:
        if example.human_status == "correct":
            correct_examples.append(example)
        elif example.human_status == "false_positive":
            false_positive_examples.append(example)
        elif example.human_status == "fixed":
            fixed_examples.append(example)

    sections: list[str] = []

    if correct_examples:
        lines = ["【過去に正しい指摘と判定された例】"]
        for index, example in enumerate(correct_examples, start=1):
            lines.append(f"{index}. AI指摘: {example.finding}")

            if example.reason:
                lines.append(f"   AI理由: {example.reason}")

            if example.suggestion:
                lines.append(f"   AI修正案: {example.suggestion}")

            if example.human_comment:
                lines.append(f"   人間コメント: {example.human_comment}")

            lines.append("   扱い: 同様の条件では指摘してよい。")

        sections.append("\n".join(lines))

    if false_positive_examples:
        lines = ["【過去に誤検出と判定された例】"]
        for index, example in enumerate(false_positive_examples, start=1):
            lines.append(f"{index}. AI指摘: {example.finding}")

            if example.reason:
                lines.append(f"   AI理由: {example.reason}")

            if example.human_comment:
                lines.append(f"   誤検出理由: {example.human_comment}")

            lines.append("   扱い: 同様の条件では指摘しないこと。")

        sections.append("\n".join(lines))

    if fixed_examples:
        lines = ["【人間が修正した指摘例】"]
        for index, example in enumerate(fixed_examples, start=1):
            lines.append(f"{index}. 元のAI指摘: {example.finding}")

            if example.corrected_finding:
                lines.append(f"   修正後の指摘: {example.corrected_finding}")

            if example.corrected_reason:
                lines.append(f"   修正後の理由: {example.corrected_reason}")

            if example.corrected_suggestion:
                lines.append(f"   修正後の修正案: {example.corrected_suggestion}")

            if example.human_comment:
                lines.append(f"   人間コメント: {example.human_comment}")

            lines.append("   扱い: 修正後の表現・判断を優先して参考にすること。")

        sections.append("\n".join(lines))

    if not sections:
        return "過去の人間レビュー結果はありません。"

    return "\n\n".join(sections)