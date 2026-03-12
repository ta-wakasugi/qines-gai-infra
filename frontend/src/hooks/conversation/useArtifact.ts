import { ArtifactType } from "@/models/conversation";
import { atom, useAtom } from "jotai";

const artifactAtom = atom<ArtifactType | null>(null);
const artifactHistoryAtom = atom<ArtifactType[]>([]);
const latestArtifactAtom = atom<ArtifactType | null>(null);
// アーティファクトID → ドキュメントIDのマッピング
const artifactToDocumentMappingAtom = atom<Record<string, string>>({});

/**
 * 成果物を管理するカスタムフック
 * @returns {Object} 成果物の状態と操作関数を含むオブジェクト
 * @property {ArtifactType | null} artifact - 現在の成果物
 * @property {Function} setArtifact - 成果物を設定する関数
 * @property {ArtifactType[]} artifactHistory - 成果物の履歴リスト
 * @property {Function} addArtifactHistory - 成果物履歴を追加する関数
 * @property {Function} setArtifactHistory - 成果物履歴を直接設定する関数
 * @property {Function} resetArtifact - 成果物をリセットする関数
 * @property {ArtifactType | null} latestArtifact - 最新の成果物
 * @property {Function} setLatestArtifact - 最新の成果物を設定する関数
 * @property {Function} getMaxVersionById - 指定IDの最大バージョンを取得する関数
 * @property {Function} getArtifactByIdAndVersion - 指定IDとバージョンの成果物を取得する関数
 * @property {Function} addArtifactToDocumentMapping - アーティファクトIDとドキュメントIDのマッピングを追加する関数
 * @property {Function} getDocumentIdByArtifactId - アーティファクトIDからドキュメントIDを取得する関数
 */
export const useArtifact = () => {
  const [artifact, setArtifact] = useAtom(artifactAtom);
  const [artifactHistory, setArtifactHistory] = useAtom(artifactHistoryAtom);
  const [latestArtifact, setLatestArtifact] = useAtom(latestArtifactAtom);
  const [artifactToDocumentMapping, setArtifactToDocumentMapping] = useAtom(
    artifactToDocumentMappingAtom
  );

  /**
   * 成果物をリセットする
   */
  const resetArtifact = () => {
    setArtifact(null);
  };

  /**
   * 成果物履歴に新しい成果物を追加する
   * @param artifact - 追加する成果物または成果物配列
   */
  const addArtifactHistory = (artifact: ArtifactType | ArtifactType[] | null) => {
    if (!artifact) {
      return;
    }
    if (Array.isArray(artifact)) {
      setArtifactHistory(artifact);
    } else {
      setArtifactHistory((prev) => [...prev, artifact]);
    }
  };

  /**
   * 指定されたIDの成果物の最大バージョンを取得する
   * @param artifactId - 成果物ID
   * @returns 最大バージョン番号
   */
  const getMaxVersionById = (artifactId: string) => {
    const targetArtifacts = artifactHistory.filter(
      (searchArtifact) => searchArtifact.id === artifactId
    );
    if (targetArtifacts.length === 0) {
      // historyにない場合はversionの最小値を返す
      return 1;
    }
    return Math.max(...targetArtifacts.map((artifact) => artifact.version));
  };

  /**
   * 指定されたIDとバージョンの成果物を取得する
   * @param artifactId - 成果物ID
   * @param version - バージョン番号
   * @returns 該当する成果物、存在しない場合はnull
   */
  const getArtifactByIdAndVersion = (artifactId: string, version: number) => {
    const targetArtifact = artifactHistory.find(
      (searchArtifact) =>
        searchArtifact.id === artifactId && searchArtifact.version === version
    );
    if (!targetArtifact) {
      return null;
    }
    return targetArtifact;
  };

  /**
   * アーティファクトIDとドキュメントIDのマッピングを追加する
   * @param artifactId - アーティファクトID
   * @param documentId - ドキュメントID
   */
  const addArtifactToDocumentMapping = (artifactId: string, documentId: string) => {
    setArtifactToDocumentMapping((prev) => ({
      ...prev,
      [artifactId]: documentId,
    }));
  };

  /**
   * アーティファクトIDからドキュメントIDを取得する
   * @param artifactId - アーティファクトID
   * @returns ドキュメントID、存在しない場合はnull
   */
  const getDocumentIdByArtifactId = (artifactId: string): string | null => {
    return artifactToDocumentMapping[artifactId] || null;
  };

  return {
    artifact,
    setArtifact,
    artifactHistory,
    addArtifactHistory,
    setArtifactHistory,
    resetArtifact,
    latestArtifact,
    setLatestArtifact,
    getMaxVersionById,
    getArtifactByIdAndVersion,
    addArtifactToDocumentMapping,
    getDocumentIdByArtifactId,
  };
};
