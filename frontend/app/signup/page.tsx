"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { UserPlus, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

/** HR + Insight 로고 — 로그인과 동일 스타일 */
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

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (): boolean => {
    if (!name.trim()) {
      setError("이름을 입력해 주세요.");
      return false;
    }
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
    if (password !== passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return false;
    }
    if (!agreeTerms) {
      setError("이용약관 및 개인정보 처리방침에 동의해 주세요.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      router.push("/login");
    } catch {
      setError("회원가입에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <LogoWordmark />
        </div>

        <div className="rounded-2xl border border-[#a8d5c4] bg-white p-8 shadow-lg dark:border-primary/30 dark:bg-card md:p-10">
          <div className="flex items-center gap-2 text-slate-800 dark:text-foreground">
            <UserPlus className="h-5 w-5 text-[#3D7D3D] dark:text-primary" />
            <h2 className="text-lg font-semibold">회원가입</h2>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-muted-foreground">
            HR Insight 계정을 만들어 보세요.
          </p>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
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
              <Label htmlFor="signup-name" className="text-slate-700 dark:text-muted-foreground">
                이름
              </Label>
              <Input
                id="signup-name"
                type="text"
                name="name"
                autoComplete="name"
                placeholder="홍길동"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                className="border-[#a8d5c4]/60 dark:border-primary/30 dark:bg-card dark:text-foreground"
                aria-invalid={!!error}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-email" className="text-slate-700 dark:text-muted-foreground">
                이메일
              </Label>
              <Input
                id="signup-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                className="border-[#a8d5c4]/60 dark:border-primary/30 dark:bg-card dark:text-foreground"
                aria-invalid={!!error}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password" className="text-slate-700 dark:text-muted-foreground">
                비밀번호
              </Label>
              <Input
                id="signup-password"
                type="password"
                name="password"
                autoComplete="new-password"
                placeholder={`${MIN_PASSWORD_LENGTH}자 이상`}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="border-[#a8d5c4]/60 dark:border-primary/30 dark:bg-card dark:text-foreground"
                aria-invalid={!!error}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password-confirm" className="text-slate-700 dark:text-muted-foreground">
                비밀번호 확인
              </Label>
              <Input
                id="signup-password-confirm"
                type="password"
                name="passwordConfirm"
                autoComplete="new-password"
                placeholder="비밀번호 다시 입력"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                disabled={loading}
                className="border-[#a8d5c4]/60 dark:border-primary/30 dark:bg-card dark:text-foreground"
                aria-invalid={!!error}
              />
            </div>

            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="signup-terms"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                disabled={loading}
                className="mt-0.5 h-4 w-4 rounded border-[#a8d5c4] text-primary focus:ring-primary/30 dark:border-primary/50"
              />
              <Label
                htmlFor="signup-terms"
                className="cursor-pointer text-sm text-slate-600 dark:text-muted-foreground"
              >
                <Link href="/terms" className="underline hover:text-[#3D7D3D] dark:hover:text-primary">
                  이용약관
                </Link>
                {" 및 "}
                <Link href="/privacy" className="underline hover:text-[#3D7D3D] dark:hover:text-primary">
                  개인정보 처리방침
                </Link>
                에 동의합니다.
              </Label>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="hero-gradient-hover mt-2 w-full gap-2 border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  가입 중...
                </>
              ) : (
                <>
                  가입하기
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500 dark:text-muted-foreground">
            이미 계정이 있으신가요?{" "}
            <Link
              href="/login"
              className="font-medium text-[#3D7D3D] hover:underline dark:text-primary"
            >
              로그인
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
