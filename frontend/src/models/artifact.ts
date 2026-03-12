import { schemas } from "@/api/openapiClient";
import { z } from "zod";

export type AddDocumentRequestType = z.infer<typeof schemas.AddDocumentRequest>;
export type AddDocumentResponseType = z.infer<typeof schemas.AddDocumentResponse>;
export type UpdateDocumentRequestType = z.infer<typeof schemas.UpdateDocumentRequest>;
export type UpdateDocumentResponseType = z.infer<typeof schemas.UpdateDocumentResponse>;
