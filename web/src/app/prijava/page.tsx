import { LoginForm } from "@/components/LoginForm";
import { redirectAuthParamsIfPresent } from "@/lib/auth-redirect";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; code?: string; token_hash?: string; type?: string }>;
}) {
  const params = await searchParams;
  redirectAuthParamsIfPresent(params, "/profil");
  return <LoginForm error={params.error ?? null} />;
}
