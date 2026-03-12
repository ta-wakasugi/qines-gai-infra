"use client";
import { atom, useAtom } from "jotai";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useError } from "./useError";
import { useButtonDisabled } from "./useButtonDisabled";

const FILE_MAX_SIZE = 2 * 1024 * 1024 * 1024; // 2GB
const uploadFileAtom = atom<File | null>(null);

/**
 * ドラッグ&ドロップでのファイルアップロードを制御するカスタムフック
 * @param {boolean} disableDrop - ドロップを無効にするかどうか
 * @returns {Object} ファイルアップロード制御に関する値とメソッド
 * @property {File|null} uploadFile - アップロードされたファイル
 * @property {Function} setUploadFile - アップロードファイルを設定するメソッド
 * @property {Function} getRootProps - ドロップゾーンのルート要素に適用するプロパティ
 * @property {Function} getInputProps - ファイル入力要素に適用するプロパティ
 * @property {boolean} isDragActive - ドラッグ中かどうかを示すフラグ
 * @property {Function} open - ファイル選択ダイアログを開くメソッド
 */
export const useDragDropUpload = (disableDrop: boolean = false) => {
  const { commonButtonDisabled } = useButtonDisabled();
  const [uploadFile, setUploadFile] = useAtom(uploadFileAtom);
  const { showError } = useError();
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) {
      showError("5MB以下のファイルをアップロードしてください");
      return;
    }
    setUploadFile(file);
  }, []);
  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    maxSize: FILE_MAX_SIZE,
    noClick: true,
    noKeyboard: true,
    disabled: commonButtonDisabled || disableDrop,
  });

  return {
    uploadFile,
    setUploadFile,
    getRootProps,
    getInputProps,
    isDragActive,
    open,
  };
};
