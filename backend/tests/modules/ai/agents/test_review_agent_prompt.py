from langchain_core.messages import HumanMessage, SystemMessage

from qines_gai_backend.modules.ai.agents.review_agent_prompt import (
    build_review_messages,
)


def test_build_review_messages_contains_rules_and_context():
    rules_text = """
[rule_id: RULE-001]
reserved bit は読み出し値、書き込み時の扱い、初期値を明記すること。
"""

    input_context_text = """
[document_id: input_doc_001]
[chunk_id: 1]
[location: ビットアサイン表]
Bit 7: reserved
"""

    messages = build_review_messages(
        rules_text=rules_text,
        input_context_text=input_context_text,
    )

    assert len(messages) == 2

    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)

    assert "ベテランノウハウ" in messages[1].content
    assert "RULE-001" in messages[1].content
    assert "Bit 7: reserved" in messages[1].content

    assert "推測" in messages[0].content or "推測" in messages[1].content
    assert "findings=[]" in messages[0].content or "findings=[]" in messages[1].content