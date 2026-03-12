import { deleteDocument, searchDocument } from "@/actions/document";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import {
  CheckboxState,
  DocumentType,
  SearchDocumentQueryType,
  UPLOADER_MAP,
  UploaderType,
} from "@/models/document";
import { atom, useAtom } from "jotai";

const LIMIT = 7; // 1ページあたりの表示件数

const inputValueAtom = atom<string>("");
const messageAtom = atom<string>("");
const pageCountAtom = atom<number>(0);
const currentPageAtom = atom<number>(0);
const searchedDocumentsAtom = atom<DocumentType[]>([]);
const collectionDocumentsAtom = atom<DocumentType[]>([]);
const checkboxStateAtom = atom<CheckboxState>({
  genre: [],
  release: [],
  uploader: [],
});

/**
 * 検索結果のドキュメントを管理するカスタムフック
 * @returns {Object} 検索結果の状態と操作関数を含むオブジェクト
 * @property {DocumentType[]} searchedDocuments - 検索されたドキュメントのリスト
 * @property {Function} setSearchedDocuments - 検索結果を設定する関数
 * @property {string[]} searchedDocumentsIds - 検索されたドキュメントのID一覧
 * @property {Function} removeDocumentFromSearched - 検索結果から指定のドキュメントを削除する関数
 */
const useSearchedDocuments = () => {
  const [searchedDocuments, setSearchedDocuments] = useAtom(searchedDocumentsAtom);
  const searchedDocumentsIds = searchedDocuments.map((d) => d.id);
  const removeDocumentFromSearched = (document: DocumentType) => {
    const newSearchedDocuments = searchedDocuments.filter((d) => d.id !== document.id);
    setSearchedDocuments(newSearchedDocuments);
    return newSearchedDocuments;
  };
  return {
    searchedDocuments,
    setSearchedDocuments,
    searchedDocumentsIds,
    removeDocumentFromSearched,
  };
};

/**
 * コレクション内のドキュメントを管理するカスタムフック
 * @returns {Object} コレクションの状態と操作関数を含むオブジェクト
 * @property {DocumentType[]} collectionDocuments - コレクション内のドキュメントリスト
 * @property {Function} setCollectionDocuments - コレクション内のドキュメントを設定する関数
 * @property {Function} addCollectionDocument - コレクションにドキュメントを追加する関数
 * @property {Function} removeDocumentFromCollection - コレクションからドキュメントを削除する関数
 * @property {string[]} collectionDocumentsIds - コレクション内のドキュメントID一覧
 * @property {Function} isExistInCollection - ドキュメントがコレクションに存在するか確認する関数
 */
const useCollectionDocuments = () => {
  const [collectionDocuments, setCollectionDocuments] = useAtom(
    collectionDocumentsAtom
  );
  const collectionDocumentsIds = collectionDocuments.map((d) => d.id);
  const addCollectionDocument = (document: DocumentType) => {
    setCollectionDocuments([...collectionDocuments, document]);
  };
  const removeDocumentFromCollection = (document: DocumentType) => {
    setCollectionDocuments(collectionDocuments.filter((d) => d.id !== document.id));
  };
  const isExistInCollection = (document: DocumentType) => {
    return collectionDocumentsIds.includes(document.id);
  };
  return {
    collectionDocuments,
    setCollectionDocuments,
    addCollectionDocument,
    removeDocumentFromCollection,
    collectionDocumentsIds,
    isExistInCollection,
  };
};

/**
 * ドキュメント検索機能を管理するカスタムフック
 * @returns {Object} 検索機能の状態と操作関数を含むオブジェクト
 * @property {string} message - 検索状態に関するメッセージ
 * @property {string} inputValue - 検索入力値
 * @property {Function} setInputValue - 検索入力値を設定する関数
 * @property {CheckboxState} checkboxState - チェックボックスの状態
 * @property {Function} setCheckboxState - チェックボックスの状態を設定する関数
 * @property {number} pageCount - 総ページ数
 * @property {Function} setPageCount - 総ページ数を設定する関数
 * @property {number} currentPage - 現在のページ
 * @property {Function} setCurrentPage - 現在のページを設定する関数
 * @property {Function} hasCondition - 検索条件が設定されているか確認する関数
 * @property {Function} getQuery - 検索クエリを生成する関数
 */
const useSearchDocuments = () => {
  const [inputValue, setInputValue] = useAtom(inputValueAtom);
  const [message, setMessage] = useAtom(messageAtom);
  const [pageCount, setPageCount] = useAtom(pageCountAtom);
  const [currentPage, setCurrentPage] = useAtom(currentPageAtom);
  const [checkboxState, setCheckboxState] = useAtom(checkboxStateAtom);
  const hasCondition = () => {
    return (
      inputValue != "" ||
      Object.values(checkboxState).some((values) => values.length > 0) // 検索条件が指定されていればtrue
    );
  };

  const getQuery = (pageIndex?: number) => {
    const genre = checkboxState.genre.join(",");
    const release = checkboxState.release.join(",");
    const uploader = Object.keys(UPLOADER_MAP).filter((key) =>
      checkboxState.uploader.includes(UPLOADER_MAP[key as keyof typeof UPLOADER_MAP])
    ) as ReadonlyArray<UploaderType>;

    return {
      q: inputValue || null,
      hits_per_page: LIMIT,
      page: pageIndex || null,
      genre: genre || null,
      release: release || null,
      uploader: uploader.length > 0 ? uploader : null,
    } as SearchDocumentQueryType;
  };

  return {
    message,
    setMessage,
    inputValue,
    setInputValue,
    checkboxState,
    setCheckboxState,
    pageCount,
    setPageCount,
    currentPage,
    setCurrentPage,
    hasCondition,
    getQuery,
  };
};

/**
 * ドキュメント検索とコレクション管理の統合機能を提供するカスタムフック
 * @returns {Object} 検索・コレクション管理の統合機能を含むオブジェクト
 * @property {DocumentType[]} searchedDocuments - 検索されたドキュメントのリスト
 * @property {Function} setSearchedDocuments - 検索結果を設定する関数
 * @property {string[]} searchedDocumentsIds - 検索されたドキュメントのID一覧
 * @property {Function} removeDocumentFromSearched - 検索結果から指定のドキュメントを削除する関数
 * @property {DocumentType[]} collectionDocuments - コレクション内のドキュメントリスト
 * @property {Function} setCollectionDocuments - コレクション内のドキュメントを設定する関数
 * @property {string[]} collectionDocumentsIds - コレクション内のドキュメントID一覧
 * @property {Function} isExistInCollection - ドキュメントがコレクションに存在するか確認する関数
 * @property {string} message - 検索状態に関するメッセージ
 * @property {string} inputValue - 検索入力値
 * @property {Function} setInputValue - 検索入力値を設定する関数
 * @property {CheckboxState} checkboxState - チェックボックスの状態
 * @property {Function} setCheckboxState - チェックボックスの状態を設定する関数
 * @property {number} pageCount - 総ページ数
 * @property {Function} setPageCount - 総ページ数を設定する関数
 * @property {number} currentPage - 現在のページ
 * @property {Function} setCurrentPage - 現在のページを設定する関数
 * @property {Function} moveToCollection - ドキュメントをコレクションに移動する関数
 * @property {Function} removeFromCollection - ドキュメントをコレクションから削除する関数
 * @property {Function} searchDocuments - ドキュメントを検索する関数
 * @property {Function} handleChangePage - ページを変更する関数
 * @property {Function} deleteUploadedDocument - アップロードされたドキュメントを削除する関数
 */
export const useSearchCollectionDocuments = () => {
  const {
    searchedDocuments,
    setSearchedDocuments,
    searchedDocumentsIds,
    removeDocumentFromSearched,
  } = useSearchedDocuments();
  const {
    collectionDocuments,
    setCollectionDocuments,
    addCollectionDocument,
    collectionDocumentsIds,
    isExistInCollection,
    removeDocumentFromCollection,
  } = useCollectionDocuments();
  const {
    message,
    setMessage,
    inputValue,
    setInputValue,
    checkboxState,
    setCheckboxState,
    pageCount,
    setPageCount,
    currentPage,
    setCurrentPage,
    hasCondition,
    getQuery,
  } = useSearchDocuments();
  const { setCommonButtonDisabled } = useButtonDisabled();
  const { showError, errorTemplate } = useError();

  /**
   * ドキュメントをコレクションに移動する
   * @param document - 移動対象のドキュメント
   */
  const moveToCollection = (document: DocumentType) => {
    if (isExistInCollection(document)) return;
    addCollectionDocument(document);
    removeDocumentFromSearched(document);
  };

  /**
   * ドキュメントをコレクションから削除する
   * @param document - 削除対象のドキュメント
   */
  const removeFromCollection = (document: DocumentType) => {
    removeDocumentFromCollection(document);
  };

  /**
   * ドキュメントを検索する
   */
  const searchDocuments = async () => {
    if (!hasCondition()) {
      setSearchedDocuments([]);
      setPageCount(0);
      setCurrentPage(0);
      return;
    }
    setCommonButtonDisabled(true);
    setMessage("検索中...");

    try {
      const res = await searchDocument(getQuery(1));
      setSearchedDocuments(res.documents);
      setPageCount(res.total_pages);
      setCurrentPage(1);
      if (res.documents.length < 1) {
        setMessage("ドキュメントが見つかりませんでした。");
      } else {
        setMessage("");
      }
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
      setSearchedDocuments([]);
      setMessage("");
    } finally {
      setCommonButtonDisabled(false);
    }
  };

  /**
   * 検索結果のページを変更する
   * @param page - 表示するページ番号
   */
  const handleChangePage = async (page: number) => {
    setCommonButtonDisabled(true);
    setMessage("");
    setCurrentPage(page);

    try {
      const res = await searchDocument(getQuery(page));
      setSearchedDocuments(res.documents);
      setPageCount(res.total_pages);
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
      setSearchedDocuments([]);
    } finally {
      setCommonButtonDisabled(false);
    }
  };

  /**
   * アップロードされたドキュメントを削除する
   * @param document - 削除対象のドキュメント
   */
  const deleteUploadedDocument = async (document: DocumentType) => {
    setCommonButtonDisabled(true);
    try {
      await deleteDocument(document.id);
      const newSearchedDocuments = removeDocumentFromSearched(document);
      removeFromCollection(document);
      if (newSearchedDocuments.length < 1) {
        setMessage(`${currentPage}ページに表示できるドキュメントはありません。`);
      }
    } catch (e) {
      console.error(e);
      showError(errorTemplate.api);
      setSearchedDocuments([]);
    } finally {
      setCommonButtonDisabled(false);
    }
  };

  return {
    searchedDocuments,
    setSearchedDocuments,
    searchedDocumentsIds,
    removeDocumentFromSearched,

    collectionDocuments,
    addCollectionDocument,
    setCollectionDocuments,
    collectionDocumentsIds,
    isExistInCollection,

    message,
    inputValue,
    setInputValue,
    checkboxState,
    setCheckboxState,
    pageCount,
    setPageCount,
    currentPage,
    setCurrentPage,
    hasCondition,

    moveToCollection,
    removeFromCollection,

    searchDocuments,
    handleChangePage,
    deleteUploadedDocument,
  };
};
