"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { LogIn, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { startOAuthLogin, type OAuthProvider } from "@/modules/auth/gatewayAuth";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 6;

/** HR + Insight 로고 — HR 포레스트 그린, Insight 틸 그라데이션 */
function LogoWordmark() {
  return (
    <div className="text-center">
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
        AI Powered HR Intelligence
      </p>
      <h1 className="mt-1 flex items-baseline justify-center gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-[#14532d] dark:text-emerald-800">
          HR
        </span>
        <span
          className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent dark:from-teal-400 dark:to-emerald-400"
          style={{
            textShadow: "0 1px 2px rgba(0,0,0,0.06)",
            WebkitBackgroundClip: "text",
          }}
        >
          Insight
        </span>
      </h1>
    </div>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<OAuthProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validate = (): boolean => {
    if (!email.trim()) {
      setError("이메일을 입력해 주세요.");
      return false;
    }
    if (!EMAIL_REGEX.test(email.trim())) {
      setError("올바른 이메일 형식이 아닙니다.");
      return false;
    }
    if (!password) {
      setError("비밀번호를 입력해 주세요.");
      return false;
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`비밀번호는 ${MIN_PASSWORD_LENGTH}자 이상이어야 합니다.`);
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!validate()) return;
    setError("계정 로그인은 Spring 게이트웨이에서 소셜(카카오·네이버·구글)로 제공합니다. 아래 소셜 버튼을 이용해 주세요.");
  };

  const handleOAuth = async (provider: OAuthProvider) => {
    setError(null);
    setOauthLoading(provider);
    try {
      await startOAuthLogin(provider);
    } catch (err) {
      setError(err instanceof Error ? err.message : "소셜 로그인을 시작할 수 없습니다. 게이트웨이(8080)가 켜져 있는지 확인해 주세요.");
      setOauthLoading(null);
    }
  };

  const handleDemoProceed = () => {
    router.push("/demo");
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <LogoWordmark />
        </div>
        <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-10 shadow-xl backdrop-blur-sm dark:border-white/10 dark:bg-slate-800/95">
          <div className="flex items-center gap-2 text-slate-800 dark:text-slate-100">
            <LogIn className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            <h2 className="text-lg font-semibold">로그인</h2>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Spring 게이트웨이(8080) OAuth로 로그인합니다. 로그인 후 대시보드로 이동합니다.
          </p>

          <div className="mt-6 space-y-3">
            <Button
              type="button"
              variant="outline"
              disabled={oauthLoading !== null}
              onClick={() => handleOAuth("kakao")}
              className="h-11 w-full border-[#FEE500] bg-[#FEE500] text-[#191919] hover:bg-[#fdd835] disabled:opacity-70"
            >
              {oauthLoading === "kakao" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  카카오 연결 중…
                </>
              ) : (
                "카카오로 로그인"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={oauthLoading !== null}
              onClick={() => handleOAuth("naver")}
              className="h-11 w-full border-[#03C75A] bg-[#03C75A] text-white hover:bg-[#02b350] disabled:opacity-70"
            >
              {oauthLoading === "naver" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  네이버 연결 중…
                </>
              ) : (
                "네이버로 로그인"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={oauthLoading !== null}
              onClick={() => handleOAuth("google")}
              className="h-11 w-full border-slate-300 bg-white text-slate-800 hover:bg-slate-50 dark:border-white/20 dark:bg-white/10 dark:text-slate-100 dark:hover:bg-white/15"
            >
              {oauthLoading === "google" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Google 연결 중…
                </>
              ) : (
                "Google로 로그인"
              )}
            </Button>
          </div>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center" aria-hidden>
              <span className="w-full border-t border-slate-200 dark:border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-slate-500 dark:bg-slate-800 dark:text-slate-400">또는 (데모)</span>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div
                role="alert"
                className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200"
              >
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="login-email" className="text-slate-700 dark:text-slate-300">
                이메일
              </Label>
              <Input
                id="login-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={oauthLoading !== null}
                className="border-slate-200 bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:placeholder:text-slate-500"
                aria-invalid={!!error}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="login-password" className="text-slate-700 dark:text-slate-300">
                  비밀번호
                </Label>
                <Link
                  href="/forgot-password"
                  className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  비밀번호 찾기
                </Link>
              </div>
              <Input
                id="login-password"
                type="password"
                name="password"
                autoComplete={rememberMe ? "current-password" : "off"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={oauthLoading !== null}
                className="border-slate-200 bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:placeholder:text-slate-500"
                aria-invalid={!!error}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="login-remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={oauthLoading !== null}
                className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 dark:border-white/20 dark:bg-white/5"
              />
              <Label
                htmlFor="login-remember"
                className="cursor-pointer text-sm text-slate-600 dark:text-slate-400"
              >
                로그인 상태 유지
              </Label>
            </div>

            <Button
              type="submit"
              disabled={oauthLoading !== null}
              variant="outline"
              className="mt-2 w-full gap-2 disabled:opacity-70"
            >
              이메일 로그인 안내
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="mt-6 border-t border-slate-200/80 pt-6 dark:border-white/10">
            <p className="text-center text-xs text-slate-500 dark:text-slate-400">
              포트폴리오 시연용
            </p>
            <Button
              type="button"
              variant="outline"
              onClick={handleDemoProceed}
              disabled={oauthLoading !== null}
              className="mt-3 w-full gap-2 border-slate-200 dark:border-white/10"
            >
              데모: 로그인 없이 역할 선택하기
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <p className="mt-5 text-center text-xs text-slate-500 dark:text-slate-400">
            계정이 없으신가요?{" "}
            <Link
              href="/signup"
              className="font-medium text-emerald-600 hover:underline dark:text-emerald-400"
            >
              회원가입
            </Link>
            {" · "}
            <Link
              href="/contact"
              className="font-medium text-slate-600 hover:underline dark:text-slate-400"
            >
              문의하기
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
