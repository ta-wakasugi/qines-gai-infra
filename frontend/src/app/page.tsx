"use client";
import { getCollectionList } from "@/actions/collection";
import { ErrorAlert } from "@/components/error/errorAlert";
import BaseHeader from "@/components/header/baseHeader";
import HelpIcon from "@/components/icons/helpIcon";
import { MessageIcon } from "@/components/icons/messageIcon";
import { PlusBoxIcon } from "@/components/icons/plusBoxIcon";
import { ChatStartInput } from "@/components/input/chatStartInput";
import PageLoading from "@/components/loading/pageLoading";
import { THEME_COLORS } from "@/consts/color";
import { DISPLAY_PATH } from "@/consts/paths";
import { useError } from "@/hooks/useError";
import { CollectionBaseType } from "@/models/collection";
import { useEffect, useState } from "react";

export default function Home() {
  const MAX_DISPLAY_CARD_COUNT = 3;
  const [collections, setCollections] = useState<CollectionBaseType[]>([]);
  const { showError, errorTemplate } = useError();

  useEffect(() => {
    (async () => {
      try {
        const collectionList = await getCollectionList(MAX_DISPLAY_CARD_COUNT);
        setCollections(collectionList.collections);
      } catch (e) {
        console.error(e);
        showError(errorTemplate.api);
      }
    })();
  }, []);

  return (
    <>
      <ErrorAlert />
      <BaseHeader />
      <PageLoading text="回答を生成しています" />
      <div className="relative flex flex-col overflow-y-auto h-[89vh]">
        <div className="w-1/2 mx-auto px-2 pt-20 text-center">
          <ChatStartInput />
        </div>
        {/* TODO: フェーズ3にてドキュメントを集めるコンポーネントを以下に作成 */}
        <div className="pt-24 flex justify-center items-center text-center">
          <div className="relative w-1/2">
            <div className="inline-flex items-center gap-3 relative">
              <div className="[font-family:'Noto_Sans_JP-SemiBold',Helvetica] font-semibold text-text text-3xl tracking-[1.20px] relative w-fit leading-[Truepx] whitespace-nowrap">
                ドキュメントを集める
              </div>
              <HelpIcon />
            </div>

            <div className="flex flex-col w-full items-center gap-10 p-5 relative top-8 left-0 bg-[#ffffffcc] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f]">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                {collections.map((collection, index) => (
                  <div
                    className="bg-[#ffffffcc] flex w-full h-[86px] items-center justify-center gap-4 px-0 py-3  rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f]"
                    key={index}
                  >
                    <div className="flex w-full h-[86px] items-center justify-center gap-4 px-0 py-3 relative mt-[-12.00px] mb-[-12.00px] rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f]">
                      <div className="flex items-center justify-center [font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal text-text text-lg tracking-[0.36px] w-full px-3">
                        <a
                          href={DISPLAY_PATH.CONVERSATION.NEW(
                            collection.public_collection_id
                          )}
                        >
                          <MessageIcon
                            className="w-5 h-5 mr-4"
                            color={THEME_COLORS.buttonDisabled}
                          />
                        </a>
                        <a
                          className="hover:underline text-ellipsis overflow-hidden whitespace-nowrap"
                          href={DISPLAY_PATH.COLLECTION.EDIT(
                            collection.public_collection_id
                          )}
                        >
                          {collection.name}
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
                <a href={DISPLAY_PATH.COLLECTION.NEW}>
                  <div className="bg-[#151dda33] flex w-full h-[86px] items-center justify-center gap-4 px-0 py-3  rounded-2xl shadow-[0px_2px_12px_#aaaaaa1f] hover:underline">
                    <PlusBoxIcon className="w-5 h-5" />
                    <div className="[font-family:'Noto_Sans_JP-Regular',Helvetica] font-normal text-action-blue text-lg text-right tracking-[0.36px] relative leading-[Truepx] whitespace-nowrap">
                      新規コレクション
                    </div>
                  </div>
                </a>
              </div>

              <a
                className="[font-family:'Noto_Sans_JP-Medium',Helvetica] font-medium text-action-blue text-base text-right tracking-[0.32px] relative w-fit leading-[Truepx] whitespace-nowrap hover:underline"
                href={DISPLAY_PATH.COLLECTION.LIST}
              >
                一覧を見る
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
