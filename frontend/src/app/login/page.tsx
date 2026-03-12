import { ErrorAlert } from "@/components/error/errorAlert";
import Image from "next/image";
import Logo from "@/components/icons/logo";
import { login } from "@/actions/auth";

type LoginPageProps = { searchParams?: { callbackUrl?: string } };

/**
 * リダイレクト先を相対パスのみに限定するためのサニタイズ処理
 * @param path リダイレクト先のURL
 * @returns サニタイズされたURL
 */
function sanitize(path?: string) {
  if (!path) return "/";
  if (path.startsWith("/") && !path.startsWith("//")) return path;
  return "/";
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  const raw = searchParams?.callbackUrl ?? "/";
  const redirectTo = sanitize(raw);

  return (
    <>
      <ErrorAlert />
      <div className="relative min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              <Image
                src="/favicon.ico"
                alt="QINeS-GAI アイコン"
                width={32}
                height={32}
                className="w-8 h-8"
              />
              <Logo disabled />
            </div>
          </div>
          <form className="flex justify-center" action={login.bind(null, redirectTo)}>
            <button
              type="submit"
              className="flex justify-center items-center font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200 px-6 py-3 text-base bg-action-blue text-white hover:bg-blue-700 focus:ring-action-blue"
            >
              ログイン
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
