"use client";

import { useRef, useState } from "react";

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
};

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

  const [task, setTask] = useState<ReviewTask | null>(null);
  const [results, setResults] = useState<ReviewResult[]>([]);

  const [uploadingKnowhow, setUploadingKnowhow] = useState(false);
  const [reviewing, setReviewing] = useState(false);

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

      setUploadedKnowhowDocIds((prev) => [...prev, docId]);
      alert("ノウハウファイルのアップロードが完了しました。");
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "アップロードに失敗しました。");
    } finally {
      setUploadingKnowhow(false);
    }
  }

  async function createReviewTask(inputDocId: string) {
    const response = await fetch(REVIEWS_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input_doc_ids: [inputDocId],
        knowhow_doc_ids: uploadedKnowhowDocIds,
        batch_size: 3,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`レビュー開始に失敗しました: ${response.status} ${text}`);
    }

    return (await response.json()) as ReviewTask;
  }

  async function fetchReviewTask(taskId: string) {
    const response = await fetch(`${REVIEWS_ENDPOINT}/${taskId}`);

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

    return (await response.json()) as ReviewResult[];
  }

  async function pollReviewTask(taskId: string) {
    while (true) {
      const latestTask = await fetchReviewTask(taskId);
      setTask(latestTask);

      if (latestTask.status === "completed") {
        const reviewResults = await fetchReviewResults(taskId);
        setResults(reviewResults);
        alert("レビューが完了しました。");
        return;
      }

      if (latestTask.status === "failed") {
        throw new Error(latestTask.error_message ?? "レビューに失敗しました。");
      }

      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }

  function getTaskId(task: ReviewTask): string {
    return task.id ?? task.task_id ?? "";
  }

  async function handleStartReview() {
    if (!dataFile) {
      alert("データファイルを選択してください。");
      return;
    }

    if (uploadedKnowhowDocIds.length === 0) {
      alert("先にノウハウファイルをアップロードしてください。");
      return;
    }

    setReviewing(true);
    setTask(null);
    setResults([]);

    try {
      const uploadedInput = await uploadDocument(dataFile, "review_input");
      const inputDocId = getUploadedDocId(uploadedInput);

      if (!inputDocId) {
        throw new Error("入力データのdoc_idを取得できませんでした。");
      }

      const createdTask = await createReviewTask(inputDocId);
      const taskId = getTaskId(createdTask);

      if (!taskId) {
        throw new Error(
          "レビュー開始レスポンスから取得されたtask_idを取得できませんでした。"
        );
      }

      setTask({ ...createdTask, id: taskId });

      await pollReviewTask(taskId);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "レビュー開始に失敗しました。");
    } finally {
      setReviewing(false);
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
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-[#f6d5ad] px-2 text-center text-base text-text"
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
                className="h-9 w-full max-w-[150px] rounded-md border border-black bg-white text-base text-text disabled:cursor-not-allowed disabled:opacity-50"
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
                className="h-9 w-full max-w-[240px] rounded-md border border-black bg-[#f6d5ad] px-2 text-center text-base text-text"
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

              <button
                type="button"
                onClick={handleStartReview}
                disabled={reviewing}
                className="h-9 w-full max-w-[150px] rounded-md border border-black bg-white text-base text-text disabled:cursor-not-allowed disabled:opacity-50"
              >
                {reviewing ? "レビュー中" : "レビュー開始"}
              </button>
            </div>
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

      {results.length > 0 && (
        <div className="mt-4 flex flex-col gap-3 text-left">
          {results.map((result) => (
            <div
              key={result.id}
              className="rounded-xl border border-gray-300 bg-white p-4 text-sm"
            >
              <div>
                <strong>重要度:</strong> {result.severity ?? "-"}
              </div>
              <div>
                <strong>対象:</strong> {result.target ?? "-"}
              </div>
              <div>
                <strong>指摘:</strong> {result.finding}
              </div>
              {result.reason && (
                <div>
                  <strong>理由:</strong> {result.reason}
                </div>
              )}
              {result.suggestion && (
                <div>
                  <strong>修正案:</strong> {result.suggestion}
                </div>
              )}
              {result.evidences?.map((evidence, index) => (
                <pre
                  key={`${result.id}-${index}`}
                  className="mt-2 whitespace-pre-wrap rounded bg-gray-100 p-2"
                >
                  {evidence.quote}
                </pre>
              ))}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
