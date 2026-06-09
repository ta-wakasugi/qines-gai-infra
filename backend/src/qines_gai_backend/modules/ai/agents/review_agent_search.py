# src/qines_gai_backend/modules/ai/agents/review_agent_search.py

import json

from .review_agent_schema import ReviewRule
from textwrap import dedent

def split_batches(
    rules: list[ReviewRule],
    batch_size: int,
) -> list[list[ReviewRule]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

    return [
        rules[i:i + batch_size]
        for i in range(0, len(rules), batch_size)
    ]


def _meili_in_filter(field: str, values: list[str]) -> str:
    quoted_values = ", ".join(
        json.dumps(value, ensure_ascii=False)
        for value in values
    )
    return f"{field} IN [{quoted_values}]"


async def load_knowhow_rules_from_meili(
    *,
    meili_client,
    index_name: str,
    knowhow_doc_ids: list[str],
    document_role: str = "review_rule",
    limit: int = 1000,
) -> list[ReviewRule]:
    index = meili_client.index(index_name)

    result = await index.search(
        query="",
        filter=[
            f'document_role = "{document_role}"',
            _meili_in_filter("doc_id", knowhow_doc_ids),
        ],
        limit=limit,
        attributes_to_retrieve=[
            "id",
            "doc_id",
            "title",
            "contents",
            "document_role",
            "page_num",
            "chunk_num",
        ],
    )

    rules: list[ReviewRule] = []

    for hit in _get_hits(result):
        content = hit.get("contents") or ""
        title = hit.get("title") or "no title"

        if not content.strip():
            continue

        rule_id = str(hit.get("id"))

        rules.append(
            ReviewRule(
                rule_id=rule_id,
                title=title,
                content=content,
                source_chunk_id=rule_id,
            )
        )

    return rules

def _get_hits(result) -> list[dict]:
    if hasattr(result, "hits"):
        return result.hits

    return result.get("hits", [])


async def load_input_contexts_from_meili(
    *,
    meili_client,
    index_name: str,
    input_doc_ids: list[str],
    document_role: str = "review_input",
    limit_per_page: int = 1000,
    max_total: int = 10000,
) -> list[dict]:
    """
    レビュー対象の入力データを全件取得する。

    重要:
    - キーワード検索はしない
    - input_doc_ids に該当するチャンクを全件取得する
    - document_role はレビューをするデータ
    """

    index = meili_client.index(index_name)

    all_hits: list[dict] = []
    offset = 0

    while len(all_hits) < max_total:
        result = await index.search(
            query="",
            filter=[
                f'document_role = "{document_role}"',
                _meili_in_filter("doc_id", input_doc_ids),
            ],
            limit=limit_per_page,
            offset=offset,
            attributes_to_retrieve=[
                "id",
                "doc_id",
                "title",
                "contents",
                "document_role",
                "page_num",
                "chunk_num",
            ],
        )

        hits = _get_hits(result)

        if not hits:
            break

        all_hits.extend(hits)

        if len(hits) < limit_per_page:
            break

        offset += limit_per_page

    return sorted(all_hits, key=_context_sort_key)


def _context_sort_key(ctx: dict):
    """
    入力データをできるだけ元の順番に近い形で並べるためのキー。
    プロジェクト側で chunk_index や order があるなら、それを優先する。
    """

    return (
        str(ctx.get("doc_id") or ctx.get("document_id") or ""),
        _to_int(ctx.get("page_num") or ctx.get("page")),
        _to_int(ctx.get("chunk_num") or ctx.get("chunk_index")),
        str(ctx.get("id") or ""),
    )

def _to_int(value) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0
    
def split_context_batches(
    contexts: list[dict],
    *,
    max_chars: int = 30000,
    max_chunks: int = 30,
) -> list[list[dict]]:
    """
    入力データ全文をAIに渡せるサイズに分割する。

    max_chars:
        1回のAIレビューに渡す最大文字数の目安。

    max_chunks:
        1回のAIレビューに渡す最大チャンク数の目安。
    """

    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_chars = 0

    for ctx in contexts:
        content = ctx.get("contents") or ctx.get("content") or ctx.get("text") or ""
        content_length = len(content)

        should_flush = (
            current_batch
            and (
                current_chars + content_length > max_chars
                or len(current_batch) >= max_chunks
            )
        )

        if should_flush:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0

        current_batch.append(ctx)
        current_chars += content_length

    if current_batch:
        batches.append(current_batch)

    return batches

def format_rules_for_prompt(batch_rules: list[ReviewRule]) -> str:
    blocks: list[str] = []

    for i, rule in enumerate(batch_rules, start=1):
        block = dedent(
            f"""
            ## Rule {i}

            rule_id: {rule.rule_id}
            title: {rule.title}

            content:
            {rule.content}
            """.strip() 
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def format_context_for_prompt(contexts: list[dict]) -> str:
    blocks: list[str] = []

    for i, ctx in enumerate(contexts, start=1):
        content = ctx.get("contents") or ctx.get("content") or ctx.get("text") or ""
        location = ctx.get("title") or ctx.get("page_num") or ""

        block = dedent(
            f"""
            ## Context {i}

            document_id: {ctx.get("doc_id") or ctx.get("document_id")}
            chunk_id: {ctx.get("id")}
            location: {location}

            content:
            {content}
            """
        ).strip()

        blocks.append(block)

    return "\n\n".join(blocks)