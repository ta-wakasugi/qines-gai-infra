# tests/modules/ai/agents/test_review_agent_search.py

import asyncio

import pytest

from qines_gai_backend.modules.ai.agents.review_agent_schema import ReviewRule
from qines_gai_backend.modules.ai.agents.review_agent_search import (
    format_context_for_prompt,
    format_rules_for_prompt,
    load_input_contexts_from_meili,
    load_knowhow_rules_from_meili,
    split_batches,
    split_context_batches,
)


class FakeSearchResult:
    """
    meilisearch_python_sdk の SearchResult 風オブジェクト。
    既存コードでは result.hits で扱う想定。
    """

    def __init__(self, hits):
        self.hits = hits


class FakeIndex:
    """
    AsyncIndex.search のFake。
    実SDKに合わせて query / filter / limit / offset / attributes_to_retrieve を
    キーワード引数で受け取る。
    """

    def __init__(self):
        self.search_calls = []

    async def search(
        self,
        query="",
        *,
        filter=None,
        limit=None,
        offset=0,
        attributes_to_retrieve=None,
        **kwargs,
    ):
        self.search_calls.append(
            {
                "query": query,
                "filter": filter,
                "limit": limit,
                "offset": offset,
                "attributes_to_retrieve": attributes_to_retrieve,
                "kwargs": kwargs,
            }
        )

        filters = filter or []

        # ノウハウルール取得用
        if 'document_role = "review_rule"' in filters:
            return FakeSearchResult(
                [
                    {
                        "id": "rule-doc-1_c0",
                        "doc_id": "rule-doc-1",
                        "title": "Signal定義確認",
                        "contents": "Signalの説明が不足していないか確認する。",
                        "document_role": "review_rule",
                        "chunk_num": 1,
                    },
                    {
                        "id": "rule-doc-1_c1",
                        "doc_id": "rule-doc-1",
                        "title": "PDU確認",
                        "contents": "PDUとSignalの対応関係を確認する。",
                        "document_role": "review_rule",
                        "chunk_num": 2,
                    },
                ]
            )

        # 入力データ取得用
        if 'document_role = "review_input"' in filters:
            all_hits = [
                {
                    "id": "input-doc-1_c0",
                    "doc_id": "input-doc-1",
                    "title": "入力データ",
                    "contents": "入力データ本文1",
                    "document_role": "review_input",
                    "page_num": 1,
                    "chunk_num": 1,
                },
                {
                    "id": "input-doc-1_c1",
                    "doc_id": "input-doc-1",
                    "title": "入力データ",
                    "contents": "入力データ本文2",
                    "document_role": "review_input",
                    "page_num": 1,
                    "chunk_num": 2,
                },
                {
                    "id": "input-doc-1_c2",
                    "doc_id": "input-doc-1",
                    "title": "入力データ",
                    "contents": "入力データ本文3",
                    "document_role": "review_input",
                    "page_num": 2,
                    "chunk_num": 3,
                },
            ]

            if limit is None:
                return FakeSearchResult(all_hits)

            return FakeSearchResult(all_hits[offset : offset + limit])

        return FakeSearchResult([])


class FakeMeiliClient:
    def __init__(self):
        self.fake_index = FakeIndex()

    def index(self, index_name):
        assert index_name == "qines-gai"
        return self.fake_index


def test_split_batches():
    rules = [
        ReviewRule(
            rule_id=f"rule-{i}",
            title=f"title-{i}",
            content=f"content-{i}",
        )
        for i in range(12)
    ]

    batches = split_batches(rules, batch_size=5)

    assert len(batches) == 3
    assert len(batches[0]) == 5
    assert len(batches[1]) == 5
    assert len(batches[2]) == 2


def test_split_batches_invalid_size():
    rules = [
        ReviewRule(
            rule_id="rule-1",
            title="title",
            content="content",
        )
    ]

    with pytest.raises(ValueError):
        split_batches(rules, batch_size=0)


def test_load_knowhow_rules_from_meili():
    async def run():
        client = FakeMeiliClient()

        rules = await load_knowhow_rules_from_meili(
            meili_client=client,
            index_name="qines-gai",
            knowhow_doc_ids=["rule-doc-1"],
            document_role="review_rule",
        )

        assert len(rules) == 2
        assert rules[0].rule_id == "rule-doc-1_c0"
        assert rules[0].title == "Signal定義確認"
        assert "Signal" in rules[0].content
        assert rules[0].source_chunk_id == "rule-doc-1_c0"

        call = client.fake_index.search_calls[0]
        assert call["query"] == ""
        assert 'document_role = "review_rule"' in call["filter"]
        assert 'doc_id IN ["rule-doc-1"]' in call["filter"]

    asyncio.run(run())


def test_load_input_contexts_from_meili():
    async def run():
        client = FakeMeiliClient()

        contexts = await load_input_contexts_from_meili(
            meili_client=client,
            index_name="qines-gai",
            input_doc_ids=["input-doc-1"],
            document_role="review_input",
            limit_per_page=2,
        )

        assert len(contexts) == 3

        assert contexts[0]["id"] == "input-doc-1_c0"
        assert contexts[1]["id"] == "input-doc-1_c1"
        assert contexts[2]["id"] == "input-doc-1_c2"

        first_call = client.fake_index.search_calls[0]
        assert first_call["query"] == ""
        assert 'document_role = "review_input"' in first_call["filter"]
        assert 'doc_id IN ["input-doc-1"]' in first_call["filter"]
        assert first_call["limit"] == 2
        assert first_call["offset"] == 0

        second_call = client.fake_index.search_calls[1]
        assert second_call["offset"] == 2

    asyncio.run(run())


def test_split_context_batches():
    contexts = [
        {"id": "c1", "contents": "a" * 10},
        {"id": "c2", "contents": "b" * 10},
        {"id": "c3", "contents": "c" * 10},
    ]

    batches = split_context_batches(
        contexts,
        max_chars=25,
        max_chunks=10,
    )

    assert len(batches) == 2
    assert len(batches[0]) == 2
    assert len(batches[1]) == 1


def test_format_rules_for_prompt():
    rules = [
        ReviewRule(
            rule_id="rule-1",
            title="Signal定義確認",
            content="Signalの説明が不足していないか確認する。",
        )
    ]

    prompt = format_rules_for_prompt(rules)

    assert "Rule 1" in prompt
    assert "rule_id: rule-1" in prompt
    assert "Signal定義確認" in prompt
    assert "Signalの説明" in prompt


def test_format_context_for_prompt():
    contexts = [
        {
            "id": "input-doc-1_c0",
            "doc_id": "input-doc-1",
            "title": "入力データ",
            "contents": "入力データ本文です。",
            "chunk_num": 1,
            "document_role": "review_input",
        }
    ]

    prompt = format_context_for_prompt(contexts)

    assert "Context 1" in prompt
    assert "document_id: input-doc-1" in prompt
    assert "chunk_id: input-doc-1_c0" in prompt
    assert "入力データ本文です。" in prompt