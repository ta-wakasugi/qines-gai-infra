import "next-auth/jwt";
import "next-auth";

declare module "next-auth/jwt" {
  interface JWT {
    access_token?: string;
    refresh_token?: string;
    id_token?: string;
    expires_at?: number;
    error?: string;
    iat?: number;
    exp?: number;
    jti?: string;
  }
}

declare module "next-auth" {
  interface Session {
    access_token?: string;
    refresh_token?: string;
    id_token?: string;
    error?: string;
  }
}

export {};
