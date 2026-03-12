"use client";
import { deleteCollection, getCollectionList } from "@/actions/collection";
import CollectionAccordion from "@/components/collection/collectionAccordion";
import { ErrorAlert } from "@/components/error/errorAlert";
import BaseHeader from "@/components/header/baseHeader";
import { PlusIcon } from "@/components/icons/plusIcon";
import Background from "@/components/utils/Background";
import Snackbar from "@/components/utils/snackbar";
import { useError } from "@/hooks/useError";
import { CollectionBaseType } from "@/models/collection";
import { useEffect, useState } from "react";

/**
 * コレクション一覧取得フック
 * @returns コレクション一覧の状態と操作関数を含むオブジェクト
 */
const useCollectionList = () => {
  const MAX_DISPLAY_COUNT = 1000;
  const [collections, setCollections] = useState<CollectionBaseType[]>([]);
  const { showError, errorTemplate } = useError();
  /**
   * コレクション削除API実行＋コレクション一覧から該当コレクション削除
   * @param collectionId - 削除対象のコレクションID
   */
  const handleDeleteCollection = async (collectionId: string) => {
    await deleteCollection(collectionId);
    const tempCollections = collections.filter(
      (collection) => collection.public_collection_id !== collectionId
    );
    setCollections(tempCollections);
  };

  useEffect(() => {
    (async () => {
      try {
        const collectionList = await getCollectionList(MAX_DISPLAY_COUNT);
        setCollections(collectionList.collections);
      } catch (e) {
        console.error(e);
        showError(errorTemplate.api);
      }
    })();
  }, []);
  return { collections, handleDeleteCollection };
};

type CollectionListHooksType = ReturnType<typeof useCollectionList>;

/**
 * コレクション一覧画面表示
 * @param hooks
 * @returns 画面表示のJSX要素
 */
const CollectionListView = (hooks: CollectionListHooksType) => {
  return (
    <>
      <ErrorAlert />
      <Snackbar showCheckIcon />
      <div className="h-screen flex flex-col">
        <Background className="w-[99%] mx-auto" />
        <BaseHeader />
        <div className="relative flex flex-col flex-1 w-1/2 mt-2 mx-auto overflow-hidden h-full">
          <div className="flex-wrap flex flex-col overflow-hidden h-full">
            <div className="[font-family:'Noto_Sans_JP-SemiBold',Helvetica] font-semibold text-text text-3xl tracking-[1.20px] w-full mb-4 leading-[Truepx] whitespace-nowrap text-center">
              コレクション一覧
            </div>
            <div className="flex flex-col items-start gap-2 flex-1 overflow-y-auto">
              {hooks.collections.map((collection, index) => (
                <div
                  key={index}
                  className="flex items-center self-stretch w-full rounded-xl"
                >
                  <CollectionAccordion
                    collection={collection}
                    handleDeleteCollection={hooks.handleDeleteCollection}
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 mb-8 flex flex-col justify-center items-center w-full">
              <a href="/collections/new">
                <PlusIcon className="w-16 h-16" />
                <div className="text-action-blue">新規追加</div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

/**
 * コレクション一覧ページのコンポーネント
 * @returns JSX.Element
 */
export default function CollectionList() {
  const hooks = useCollectionList();
  return <CollectionListView {...hooks} />;
}
