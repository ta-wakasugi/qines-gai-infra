from typing import Literal, TypedDict

from pydantic import BaseModel, Field

class ReviewRule(BaseModel):
    rule_id: str = Field(description="ノウハウルールを一意に識別するID")
    title: str = Field(description="ノウハウルールの見出し")
    content: str = Field(description="ノウハウルールの本文")
    source_chunk_id: str | None = Field(default=None, description="Meilisearch上のチャンクID")


class Evidence(BaseModel):
    document_id: str | None = Field(default=None, description="根拠となるドキュメントID")
    chunk_id: str | None = Field(default=None, description="根拠となるチャンクID")
    location: str | None = Field(default=None, description="章番号、見出し、ページ番号など")
    quote: str = Field(description="判断根拠となる短い引用")
    

class ReviewFinding(BaseModel):
    rule_id: str = Field(description="対象のノウハウルールID")

    status: Literal["ng", "unknown"] = Field(
        description="ng=指摘あり、unknown=判定不能。問題なしは出力しない"
    )

    severity: Literal["low", "medium", "high"] = Field(
        description="指摘の重大度"
    )

    target: str | None = Field(
        default=None,
        description="指摘対象。Signal名、PDU名、章番号など"
    )

    finding: str = Field(description="指摘内容")
    reason: str = Field(description="なぜ問題と判断したか")
    suggestion: str = Field(description="修正案または確認観点")

    evidences: list[Evidence] = Field(
        default_factory=list,
        description="判断根拠"
    )


class ReviewBatchOutput(BaseModel):
    findings: list[ReviewFinding] = Field(
        default_factory=list,
        description="AIが検出した指摘一覧。問題なしのルールは含めない"
    )
    
class ReviewAgentState(TypedDict, total=False):
    task_id: int

    input_doc_ids: list[str]
    knowhow_doc_ids: list[str]
    batch_size: int

    rules: list[ReviewRule]
    rule_batches: list[list[ReviewRule]]
    
    # レビュー対象入力データ
    input_contexts: list[dict]
    context_batches: list[list[dict]]

    # 二重ループ用index
    current_rule_batch_index: int
    current_context_batch_index: int

    total_rules: int
    completed_rules: int
    

    last_findings: list[ReviewFinding]
    error_message: str | None