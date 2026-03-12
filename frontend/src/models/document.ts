import { schemas } from "@/api/openapiClient";
import { z } from "zod";

export type SearchedDocumentsType = z.infer<typeof schemas.SearchDocumentsResponse>;
export type DocumentType = z.infer<typeof schemas.DocumentBase>;
export type UploaderType = "user" | "admin";
export type SearchDocumentQueryType = {
  q?: string | null | undefined;
  genre?: string | null | undefined;
  release?: string | null | undefined;
  page?: number | undefined;
  hits_per_page?: number | undefined;
  uploader?: ReadonlyArray<UploaderType> | null | undefined;
};
export type CheckboxCategory = "genre" | "release" | "uploader";
export type CheckboxState = {
  [key in CheckboxCategory]: string[];
};

export const AUTOSAR = "AUTOSAR";
export const GENRE_LIST = ["EXP", "PRS", "SRS", "SWS", "TPS", "TR"];
export const RELEASE_LIST = ["R4-2-2", "R22-11", "R23-11"];
export const UPLOADER_MAP = {
  admin: "プリセット",
  user: "アップロード",
};
export const CATEGORY_MAPPING = {
  genre: {
    title: "ジャンル",
    items: GENRE_LIST,
  },
  release: {
    title: "リリース",
    items: RELEASE_LIST,
  },
  uploader: {
    title: "検索対象のファイル",
    items: Object.values(UPLOADER_MAP),
  },
};
