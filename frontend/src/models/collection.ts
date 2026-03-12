import { schemas } from "@/api/openapiClient";
import { z } from "zod";

export type CreateCollectionRequestType = z.infer<
  typeof schemas.CreateCollectionRequest
>;
export type CollectionBaseType = z.infer<typeof schemas.CollectionBase>;
export type CollectionDetailType = z.infer<typeof schemas.CollectionDetail>;
export type UpdateCollectionRequestType = z.infer<
  typeof schemas.CreateCollectionRequest
>;
export type SharedCollectionType = z.infer<typeof schemas.SharedCollection>;
