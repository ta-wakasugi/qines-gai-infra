"use client";

import { useRef, useState, useEffect } from "react";

type UploadedDocument = {
  id?: string;
  doc_id?: string;
  document_id?: string;
  name?: string;
  title?: string;
  document_role?: string;
};

type ReviewTask = {
  id?: string;
  task_id?: string;
  status: "pending" | "running" | "completed" | "failed";
  total_rules: number;
  completed_rules: number;
  error_message?: string | null;
};

type Evidence = {
  quote?: string;
  document_id?: string;
  chunk_id?: string;
  location?: string;
};

type ReviewResult = {
  id: string;
  task_id: string;
  rule_id: string;
  status: string;
  severity?: string | null;
  target?: string | null;
  finding: string;
  reason?: string | null;
  suggestion?: string | null;
  evidences?: Evidence[];

  human_status?: string;
  human_comment?: string;
  corrected_finding?: string;
  corrected_reason?: string;
  corrected_suggestion?: string;
  reviewed_at?: string;
};

type ReviewResultsResponse =
  | ReviewResult[]
  | {
      results?: ReviewResult[];
      review_results?: ReviewResult[];
      items?: ReviewResult[];
    };

type ReviewDocument = {
  doc_id: string;
  file_name?: string;
  document_role: "review_rule" | "review_input";
  created_at?: string;
  updated_at?: string;
};

type ResultFeedbackDraft = {
  human_status?: string;
  human_comment?: string;
  corrected_finding?: string;
  corrected_reason?: string;
  corrected_suggestion?: string;
};

function normalizeReviewResults(json: ReviewResultsResponse): ReviewResult[] {
  if (Array.isArray(json)) {
    return json;
  }

  if (Array.isArray(json.results)) {
    return json.results;
  }

  if (Array.isArray(json.review_results)) {
    return json.review_results;
  }

  if (Array.isArray(json.items)) {
    return json.items;
  }

  return [];
}

const UPLOAD_ENDPOINT = "/api/reviews/upload";
const REVIEWS_ENDPOINT = "/api/reviews";

function getUploadedDocId(uploaded: UploadedDocument): string {
  return uploaded.doc_id ?? uploaded.document_id ?? uploaded.id ?? "";
}

export default function VeteranKnowhowReview() {
  const knowhowFileInputRef = useRef<HTMLInputElement | null>(null);
  const dataFileInputRef = useRef<HTMLInputElement | null>(null);

  const [knowhowType, setKnowhowType] = useState("CANベテラン分析");
  const [reviewKnowhowType, setReviewKnowhowType] = useState("CANベテラン分析");

  const [knowhowFile, setKnowhowFile] = useState<File | null>(null);
  const [dataFile, setDataFile] = useState<File | null>(null);

  const [uploadedKnowhowDocIds, setUploadedKnowhowDocIds] = useState<string[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string>("");
  const [task, setTask] = useState<ReviewTask | null>(null);

  const [results, setResults] = useState<ReviewResult[]>([]);
  const [resultsLoaded, setResultsLoaded] = useState(false);
  const [resultError, setResultError] = useState<string | null>(null);

  const [uploadingKnowhow, setUploadingKnowhow] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  const [reviewRules, setReviewRules] = useState<ReviewDocument[]>([]);
  const [reviewInputs, setReviewInputs] = useState<ReviewDocument[]>([]);
  const [selectedKnowhowDocIds, setSelectedKnowhowDocIds] = useState<string[]>([]);
  const [selectedInputDocId, setSelectedInputDocId] = useState<string>("");

  const [documentListError, setDocumentListError] = useState<string>("");
  const [deletingDocId, setDeletingDocId] = useState<string>("");

  const [feedbackDrafts, setFeedbackDrafts] = useState<
    Record<string, ResultFeedbackDraft>
  >({});

  const [savingFeedbackResultId, setSavingFeedbackResultId] = useState<string>("");
  const [feedbackError, setFeedbackError] = useState<string>("");

  async function uploadDocument(file: File, documentRole: string) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("subject", "others");
    formData.append("document_role", documentRole);

    const response = await fetch(UPLOAD_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`アップロードに失敗しました: ${response.status} ${text}`);
    }

    return (await response.json()) as UploadedDocument;
  }

  async function handleUploadKnowhow() {
    if (!knowhowFile) {
      alert("ノウハウファイルを選択してください。");
      return;
    }

    setUploadingKnowhow(true);

    try {
      const uploaded = await uploadDocument(knowhowFile, "review_rule");
      const docId = getUploadedDocId(uploaded);

      if (!docId) {
        throw new Error("アップロード結果からdoc_idを取得できませんでした。");
      }

      setUploadedKnowhowDocIds((prev) => {
        if (prev.includes(docId)) return prev;
        return [...prev, docId];
      });

      setSelectedKnowhowDocIds((prev) => {
        if (prev.includes(docId)) return prev;
        return [...prev, docId];
      });

      setKnowhowFile(null);
      if (knowhowFileInputRef.current) {
        knowhowFileInputRef.current.value = "";
      }

      await fetchReviewDocuments();

      alert("ノウハウファイルのアップロードが完了しました。");
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "アップロードに失敗しました。");
    } finally {
      setUploadingKnowhow(false);
    }
  }

  async function createReviewTask(inputDocId: string, knowhowDocIds: string[]) {
    const response = await fetch(REVIEWS_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input_doc_ids: [inputDocId],
        knowhow_doc_ids: knowhowDocIds,
        batch_size: 3,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`レビュー開始に失敗しました: ${response.status} ${text}`);
    }

    return (await response.json()) as ReviewTask;
  }

  async function fetchReviewTask(taskId: string): Promise<ReviewTask> {
    const response = await fetch(`${REVIEWS_ENDPOINT}/${taskId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`レビュー状態取得に失敗しました: ${response.status} ${text}`);
    }

    return (await response.json()) as ReviewTask;
  }

  async function fetchReviewResults(taskId: string) {
    const response = await fetch(`${REVIEWS_ENDPOINT}/${taskId}/results`);

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`レビュー結果取得に失敗しました: ${response.status} ${text}`);
    }

    const json = (await response.json()) as ReviewResultsResponse;
    return normalizeReviewResults(json);
  }

  async function fetchReviewDocuments() {
    setDocumentListError("");

    try {
      const [rulesRes, inputsRes] = await Promise.all([
        fetch("/api/reviews/documents?document_role=review_rule"),
        fetch("/api/reviews/documents?document_role=review_input"),
      ]);

      if (!rulesRes.ok) {
        throw new Error("登録済みノウハウ一覧の取得に失敗しました");
      }

      if (!inputsRes.ok) {
        throw new Error("登録済みテストデータ一覧の取得に失敗しました");
      }

      const rules = await rulesRes.json();
      const inputs = await inputsRes.json();

      setReviewRules(rules);
      setReviewInputs(inputs);
    } catch (e) {
      console.error(e);
      setDocumentListError(
        e instanceof Error ? e.message : "登録済みデータ一覧の取得に失敗しました。"
      );
    }
  }

  useEffect(() => {
    fetchReviewDocuments();
  }, []);

  async function pollReviewTask(taskId: string) {
    const maxPollCount = 120;

    for (let i = 0; i < maxPollCount; i++) {
      const fetchedTask = await fetchReviewTask(taskId);
      const latestTask = normalizeReviewTask(fetchedTask, taskId);

      setCurrentTaskId(getTaskId(latestTask) || taskId);
      setTask(latestTask);

      if (latestTask.status === "completed") {
        const reviewResults = await fetchReviewResults(taskId);
        setResults(reviewResults);
        initializeFeedbackDrafts(reviewResults);
        setResultsLoaded(true);
        setResultError(null);
        alert("レビューが完了しました。");
        return;
      }

      if (latestTask.status === "failed") {
        throw new Error(latestTask.error_message ?? "レビューに失敗しました。");
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    throw new Error("レビューの状態確認がタイムアウトしました。");
  }

  function normalizeId(value?: string | null): string {
    if (!value) return "";
    if (value === "undefined") return "";
    if (value === "null") return "";
    return value;
  }

  function getTaskId(task?: ReviewTask | null): string {
    return normalizeId(task?.id) || normalizeId(task?.task_id);
  }

  function normalizeReviewTask(task: ReviewTask, fallbackTaskId: string): ReviewTask {
    const normalizedTaskId = getTaskId(task) || fallbackTaskId;

    return {
      ...task,
      id: task.id ?? task.task_id ?? fallbackTaskId,
      task_id: normalizedTaskId,
      total_rules: task.total_rules ?? 0,
      completed_rules: task.completed_rules ?? 0,
    };
  }

  async function handleStartReview() {
    const knowhowDocIds =
      selectedKnowhowDocIds.length > 0 ? selectedKnowhowDocIds : uploadedKnowhowDocIds;

    if (knowhowDocIds.length === 0) {
      alert("レビューに使用するノウハウを1件以上選択してください。");
      return;
    }

    setReviewing(true);
    setTask(null);
    setCurrentTaskId("");
    setResults([]);
    setResultsLoaded(false);
    setResultError(null);
    setFeedbackError("");
    setFeedbackDrafts({});

    try {
      let inputDocId = selectedInputDocId;

      if (dataFile) {
        const uploadedInput = await uploadDocument(dataFile, "review_input");
        inputDocId = getUploadedDocId(uploadedInput);

        if (!inputDocId) {
          throw new Error("入力データのdoc_idを取得できませんでした。");
        }

        setSelectedInputDocId(inputDocId);
        setDataFile(null);

        if (dataFileInputRef.current) {
          dataFileInputRef.current.value = "";
        }

        await fetchReviewDocuments();
      }

      if (!inputDocId) {
        throw new Error(
          "レビュー対象のテストデータを選択するか、データファイルを選択してください。"
        );
      }

      const createdTask = await createReviewTask(inputDocId, knowhowDocIds);
      const taskId = getTaskId(createdTask);

      if (!taskId) {
        throw new Error("レビュー開始レスポンスからtask_idを取得できませんでした。");
      }

      setCurrentTaskId(taskId);
      setTask({ ...createdTask, id: taskId, task_id: taskId });

      await pollReviewTask(taskId);
    } catch (e) {
      console.error(e);
      const message = e instanceof Error ? e.message : "レビュー開始に失敗しました。";
      setResultError(message);
      alert(message);
    } finally {
      setReviewing(false);
    }
  }

  async function deleteReviewDocument(docId: string) {
    const ok = window.confirm(
      "このドキュメントを削除しますか？\nDB、Meilisearch、S3から削除されます。"
    );

    if (!ok) return;

    setDeletingDocId(docId);
    setDocumentListError("");

    try {
      const res = await fetch(`/api/reviews/documents/${docId}`, {
        method: "DELETE",
      });

      if (!res.ok && res.status !== 204) {
        const text = await res.text().catch(() => "");
        throw new Error(
          `ドキュメントの削除に失敗しました: status=${res.status} body=${text}`
        );
      }

      setSelectedKnowhowDocIds((prev) => prev.filter((id) => id !== docId));
      setUploadedKnowhowDocIds((prev) => prev.filter((id) => id !== docId));

      if (selectedInputDocId === docId) {
        setSelectedInputDocId("");
      }

      await fetchReviewDocuments();
    } catch (e) {
      console.error(e);
      setDocumentListError(
        e instanceof Error ? e.message : "ドキュメントの削除に失敗しました"
      );
    } finally {
      setDeletingDocId("");
    }
  }

  function initializeFeedbackDrafts(reviewResults: ReviewResult[]) {
    const drafts: Record<string, ResultFeedbackDraft> = {};

    for (const result of reviewResults) {
      drafts[result.id] = {
        human_status: result.human_status ?? "",
        human_comment: result.human_comment ?? "",
        corrected_finding: result.corrected_finding ?? "",
        corrected_reason: result.corrected_reason ?? "",
        corrected_suggestion: result.corrected_suggestion ?? "",
      };
    }

    setFeedbackDrafts(drafts);
  }

  function toggleKnowhowDocId(docId: string) {
    setSelectedKnowhowDocIds((prev) => {
      if (prev.includes(docId)) {
        return prev.filter((id) => id !== docId);
      }

      return [...prev, docId];
    });
  }

  function selectInputDocId(docId: string) {
    setSelectedInputDocId(docId);
  }

  function updateFeedbackDraft(resultId: string, patch: Partial<ResultFeedbackDraft>) {
    setFeedbackDrafts((prev) => ({
      ...prev,
      [resultId]: {
        ...prev[resultId],
        ...patch,
      },
    }));
  }

  async function saveResultFeedback(resultId: string) {
    const targetResult = results.find((result) => result.id === resultId);

    const taskId =
      normalizeId(currentTaskId) ||
      normalizeId(targetResult?.task_id) ||
      getTaskId(task);

    if (!taskId) {
      setFeedbackError("task_idを取得できないため、フィードバックを保存できません。");
      return;
    }

    const draft = feedbackDrafts[resultId];

    if (!draft) {
      setFeedbackError("保存対象のフィードバック情報がありません。");
      return;
    }

    setSavingFeedbackResultId(resultId);
    setFeedbackError("");

    try {
      const url =
        `${REVIEWS_ENDPOINT}/${encodeURIComponent(taskId)}` +
        `/results/${encodeURIComponent(resultId)}`;

      console.log("saveResultFeedback url:", url);
      console.log("saveResultFeedback taskId:", taskId);
      console.log("saveResultFeedback resultId:", resultId);

      const response = await fetch(url, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          human_status: draft.human_status || null,
          human_comment: draft.human_comment ?? "",
          corrected_finding: draft.corrected_finding ?? "",
          corrected_reason: draft.corrected_reason ?? "",
          corrected_suggestion: draft.corrected_suggestion ?? "",
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          `フィードバックの保存に失敗しました: ${response.status} ${text}`
        );
      }

      const refreshedResults = await fetchReviewResults(taskId);
      setResults(refreshedResults);
      initializeFeedbackDrafts(refreshedResults);
    } catch (e) {
      console.error(e);
      setFeedbackError(
        e instanceof Error ? e.message : "フィードバックの保存に失敗しました。"
      );
    } finally {
      setSavingFeedbackResultId("");
    }
  }

  const progress =
    task && task.total_rules > 0
      ? Math.round((task.completed_rules / task.total_rules) * 100)
      : 0;

  return (
    <section className="w-full text-center">
      <h2 className="[font-family:'Noto_Sans_JP-SemiBold',Helvetica] font-semibold text-text text-3xl tracking-[1.20px] whitespace-nowrap">
        ベテランノウハウレビュー
      </h2>

      <div className="mt-6 rounded-[28px] border border-black bg-[#ffffffcc] px-4 py-3 shadow-[0px_2px_12px_#aaaaaa1f]">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-[20px] border border-black bg-white px-4 py-3">
            <h3 className="[font-family:'Noto_Sans_JP-Regular',Helvetica] text-lg font-normal text-text">
              ベテランノウハウの追加
            </h3>

            <div className="mt-3 flex flex-col items-center gap-2">
              <select
                value={knowhowType}
                onChange={(e) => setKnowhowType(e.target.value)}
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-white px-2 text-center text-base text-text"
              >
                <option value="CANベテラン分析">CANベテラン分析</option>
                <option value="コードベテラン分析">コードベテラン分析</option>
                <option value="新規ノウハウ追加">新規ノウハウ追加</option>
              </select>

              <input
                ref={knowhowFileInputRef}
                type="file"
                accept=".md,.txt"
                className="hidden"
                onChange={(e) => {
                  setKnowhowFile(e.target.files?.[0] ?? null);
                }}
              />

              <button
                type="button"
                onClick={() => knowhowFileInputRef.current?.click()}
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-white text-base text-text"
              >
                ノウハウファイル
              </button>

              <input
                readOnly
                value={knowhowFile?.name ?? ""}
                placeholder="選択されたファイル名"
                className="h-9 w-full max-w-[240px] rounded-md border border-gray-300 bg-gray-50 px-2 text-sm text-text"
              />

              <button
                type="button"
                onClick={handleUploadKnowhow}
                disabled={uploadingKnowhow}
                className="h-9 w-full max-w-[150px] rounded-md border border-black bg-[#f6d5ad] text-base text-text disabled:cursor-not-allowed disabled:opacity-50"
              >
                {uploadingKnowhow ? "アップロード中" : "アップロード"}
              </button>

              {uploadedKnowhowDocIds.length > 0 && (
                <div className="mt-2 w-full max-w-[240px] text-left text-xs text-gray-600">
                  <div>登録済みノウハウ:</div>
                  {uploadedKnowhowDocIds.map((docId) => (
                    <div key={docId} className="truncate">
                      {docId}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="rounded-[20px] border border-black bg-white px-4 py-3">
            <h3 className="[font-family:'Noto_Sans_JP-Regular',Helvetica] text-lg font-normal text-text">
              ベテランノウハウレビュー
            </h3>

            <div className="mt-3 flex flex-col items-center gap-2">
              <select
                value={reviewKnowhowType}
                onChange={(e) => setReviewKnowhowType(e.target.value)}
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-white px-2 text-center text-base text-text"
              >
                <option value="CANベテラン分析">CANベテラン分析</option>
                <option value="コードベテラン分析">コードベテラン分析</option>
                <option value="新規ノウハウ追加">新規ノウハウ追加</option>
              </select>

              <input
                ref={dataFileInputRef}
                type="file"
                accept=".md,.txt"
                className="hidden"
                onChange={(e) => {
                  setDataFile(e.target.files?.[0] ?? null);
                }}
              />

              <button
                type="button"
                onClick={() => dataFileInputRef.current?.click()}
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-white text-base text-text"
              >
                データファイル
              </button>

              <input
                readOnly
                value={dataFile?.name ?? ""}
                placeholder="選択されたファイル名"
                className="h-9 w-full max-w-[240px] rounded-md border border-gray-300 bg-gray-50 px-2 text-sm text-text"
              />

              <div className="w-full max-w-[240px] text-left text-xs text-gray-600">
                <div>選択中ノウハウ: {selectedKnowhowDocIds.length}件</div>
                <div>
                  選択中テストデータ:{" "}
                  {selectedInputDocId ? selectedInputDocId : "未選択"}
                </div>
                {dataFile && (
                  <div className="text-blue-700">
                    新規ファイルをアップロードしてレビューします。
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={handleStartReview}
                disabled={reviewing}
                className="h-9 w-full max-w-[150px] rounded-md border border-black bg-[#f6d5ad] text-base text-text disabled:cursor-not-allowed disabled:opacity-50"
              >
                {reviewing ? "レビュー中" : "レビュー開始"}
              </button>
            </div>
          </div>
        </div>

        {documentListError && (
          <div className="mt-4 rounded-xl border border-red-300 bg-red-50 p-3 text-left text-sm text-red-700">
            <strong>登録済みデータ一覧エラー:</strong> {documentListError}
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-[20px] border border-gray-300 bg-white px-4 py-3 text-left">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-bold">登録済みノウハウ</h3>
              <button
                type="button"
                onClick={fetchReviewDocuments}
                className="rounded-md border border-gray-300 px-2 py-1 text-xs"
              >
                再読込
              </button>
            </div>

            {reviewRules.length === 0 ? (
              <p className="text-sm text-gray-600">登録済みノウハウはありません。</p>
            ) : (
              <div className="flex flex-col gap-2">
                {reviewRules.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className="flex items-center justify-between gap-2 rounded-md border border-gray-200 p-2"
                  >
                    <label className="flex min-w-0 flex-1 items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={selectedKnowhowDocIds.includes(doc.doc_id)}
                        onChange={() => toggleKnowhowDocId(doc.doc_id)}
                      />
                      <span className="truncate">{doc.file_name ?? doc.doc_id}</span>
                    </label>

                    <button
                      type="button"
                      onClick={() => deleteReviewDocument(doc.doc_id)}
                      disabled={deletingDocId === doc.doc_id || reviewing}
                      className="rounded-md border border-red-300 px-2 py-1 text-xs text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {deletingDocId === doc.doc_id ? "削除中" : "削除"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-[20px] border border-gray-300 bg-white px-4 py-3 text-left">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-bold">登録済みテストデータ</h3>
              <button
                type="button"
                onClick={fetchReviewDocuments}
                className="rounded-md border border-gray-300 px-2 py-1 text-xs"
              >
                再読込
              </button>
            </div>

            {reviewInputs.length === 0 ? (
              <p className="text-sm text-gray-600">
                登録済みテストデータはありません。
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {reviewInputs.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className="flex items-center justify-between gap-2 rounded-md border border-gray-200 p-2"
                  >
                    <label className="flex min-w-0 flex-1 items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name="reviewInputDoc"
                        checked={selectedInputDocId === doc.doc_id}
                        onChange={() => selectInputDocId(doc.doc_id)}
                      />
                      <span className="truncate">{doc.file_name ?? doc.doc_id}</span>
                    </label>

                    <button
                      type="button"
                      onClick={() => deleteReviewDocument(doc.doc_id)}
                      disabled={deletingDocId === doc.doc_id || reviewing}
                      className="rounded-md border border-red-300 px-2 py-1 text-xs text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {deletingDocId === doc.doc_id ? "削除中" : "削除"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {task && (
        <div className="mt-4 rounded-xl border border-gray-300 bg-white p-4 text-left text-sm">
          <div>
            <strong>task_id:</strong> {task.id}
          </div>
          <div>
            <strong>status:</strong> {task.status}
          </div>
          <div>
            <strong>progress:</strong>{" "}
            {`${task.completed_rules} / ${task.total_rules} (${progress}%)`}
          </div>
        </div>
      )}

      {resultError && (
        <div className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-left text-sm text-red-700">
          <strong>エラー:</strong> {resultError}
        </div>
      )}

      {feedbackError && (
        <div className="mt-4 rounded-xl border border-red-300 bg-red-50 p-4 text-left text-sm text-red-700">
          <strong>フィードバック保存エラー:</strong> {feedbackError}
        </div>
      )}

      {task?.status === "completed" && resultsLoaded && results.length === 0 && (
        <div className="mt-4 rounded-xl border border-gray-300 bg-white p-4 text-left text-sm">
          <h3 className="text-base font-bold">AIレビュー結果</h3>
          <p className="mt-2 text-gray-700">指摘事項はありませんでした。</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-4 rounded-xl border border-gray-300 bg-white p-4 text-left">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold">AIレビュー結果</h3>
            <span className="text-sm text-gray-600">{results.length}件の指摘</span>
          </div>

          <div className="mt-4 flex flex-col gap-3">
            {results.map((result, index) => (
              <div
                key={result.id}
                className="rounded-xl border border-gray-300 bg-white p-4 text-sm"
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="font-bold">
                    #{index + 1} {result.target ?? "対象不明"}
                  </div>
                  <span className="rounded-full border border-gray-300 px-2 py-1 text-xs">
                    {result.severity ?? "-"}
                  </span>
                </div>

                <div className="mt-2">
                  <strong>指摘:</strong>
                  <div className="mt-1 whitespace-pre-wrap">{result.finding}</div>
                </div>

                {result.reason && (
                  <div className="mt-3">
                    <strong>理由:</strong>
                    <div className="mt-1 whitespace-pre-wrap">{result.reason}</div>
                  </div>
                )}

                {result.suggestion && (
                  <div className="mt-3">
                    <strong>修正案:</strong>
                    <div className="mt-1 whitespace-pre-wrap">{result.suggestion}</div>
                  </div>
                )}

                <div className="mt-3 text-xs text-gray-500">
                  <div>
                    <strong>rule_id:</strong> {result.rule_id ?? "-"}
                  </div>
                  <div>
                    <strong>status:</strong> {result.status ?? "-"}
                  </div>
                </div>

                {result.evidences && result.evidences.length > 0 && (
                  <div className="mt-3">
                    <strong>根拠:</strong>
                    <div className="mt-2 flex flex-col gap-2">
                      {result.evidences.map((evidence, evidenceIndex) => (
                        <div
                          key={`${result.id}-${evidenceIndex}`}
                          className="rounded bg-gray-100 p-2"
                        >
                          {evidence.location && (
                            <div className="mb-1 text-xs text-gray-500">
                              location: {evidence.location}
                            </div>
                          )}

                          {evidence.document_id && (
                            <div className="mb-1 text-xs text-gray-500">
                              document_id: {evidence.document_id}
                            </div>
                          )}

                          {evidence.chunk_id && (
                            <div className="mb-1 text-xs text-gray-500">
                              chunk_id: {evidence.chunk_id}
                            </div>
                          )}

                          <pre className="whitespace-pre-wrap text-xs">
                            {evidence.quote ?? "根拠テキストなし"}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-3">
                  <div className="font-bold text-blue-900">人間レビュー</div>

                  <div className="mt-3">
                    <label className="block text-sm font-bold">判定</label>
                    <select
                      value={feedbackDrafts[result.id]?.human_status ?? ""}
                      onChange={(e) =>
                        updateFeedbackDraft(result.id, {
                          human_status: e.target.value,
                        })
                      }
                      className="mt-1 h-9 w-full rounded-md border border-gray-300 bg-white px-2 text-sm"
                    >
                      <option value="">未判定</option>
                      <option value="correct">正しい指摘</option>
                      <option value="false_positive">誤検出</option>
                      <option value="pending">保留</option>
                      <option value="fixed">修正済み</option>
                      <option value="needs_knowhow_update">ノウハウ改善が必要</option>
                    </select>
                  </div>

                  <div className="mt-3">
                    <label className="block text-sm font-bold">コメント</label>
                    <textarea
                      value={feedbackDrafts[result.id]?.human_comment ?? ""}
                      onChange={(e) =>
                        updateFeedbackDraft(result.id, {
                          human_comment: e.target.value,
                        })
                      }
                      placeholder="判定理由、修正内容、ノウハウ改善案などを入力"
                      className="mt-1 min-h-[80px] w-full rounded-md border border-gray-300 bg-white p-2 text-sm"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => saveResultFeedback(result.id)}
                    disabled={savingFeedbackResultId === result.id}
                    className="mt-3 rounded-md border border-black bg-[#f6d5ad] px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {savingFeedbackResultId === result.id ? "保存中..." : "判定を保存"}
                  </button>

                  {result.reviewed_at && (
                    <div className="mt-2 text-xs text-gray-500">
                      保存日時: {result.reviewed_at}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
