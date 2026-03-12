import { auth } from "@/auth";
import { NextResponse } from "next/server";

const AUTH_PROVIDER = process.env.AUTH_PROVIDER;

export default auth((req) => {
  // Keycloak認証以外の場合は何もしない
  if (AUTH_PROVIDER !== "keycloak") {
    return NextResponse.next();
  }

  const { nextUrl } = req;
  const hasValid = !!req.auth?.access_token && !req.auth?.error;
  const isLoginPage = nextUrl.pathname === "/login";

  // 未認証でログイン画面以外にアクセスした場合
  if (!hasValid && !isLoginPage) {
    const callbackUrl = encodeURIComponent(nextUrl.pathname + nextUrl.search);
    const loginUrl = new URL(`/login?callbackUrl=${callbackUrl}`, nextUrl);
    return NextResponse.redirect(loginUrl);
  }

  // 認証済みでログイン画面にアクセスした場合
  if (hasValid && isLoginPage) {
    return NextResponse.redirect(new URL("/", nextUrl));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
