import { redirect } from "next/navigation";

type AuthSearchParams = {
  code?: string;
  token_hash?: string;
  type?: string;
};

/** Preusmjeri magic-link ?code= na /auth/callback prije provjere sesije. */
export function redirectAuthParamsIfPresent(params: AuthSearchParams, next: string): void {
  if (params.code) {
    const q = new URLSearchParams({ code: params.code, next });
    redirect(`/auth/callback?${q}`);
  }
  if (params.token_hash && params.type) {
    const q = new URLSearchParams({
      token_hash: params.token_hash,
      type: params.type,
      next,
    });
    redirect(`/auth/callback?${q}`);
  }
}
