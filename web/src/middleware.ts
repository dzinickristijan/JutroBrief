import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  // Magic link ponekad stigne na /profil?code=... umjesto /auth/callback
  const code = searchParams.get("code");
  if (code && pathname !== "/auth/callback") {
    const callback = request.nextUrl.clone();
    callback.pathname = "/auth/callback";
    callback.searchParams.set("code", code);
    if (!callback.searchParams.has("next")) {
      callback.searchParams.set("next", pathname === "/" ? "/profil" : pathname);
    }
    return NextResponse.redirect(callback);
  }

  const tokenHash = searchParams.get("token_hash");
  const type = searchParams.get("type");
  if (tokenHash && type && pathname !== "/auth/callback") {
    const callback = request.nextUrl.clone();
    callback.pathname = "/auth/callback";
    callback.searchParams.set("token_hash", tokenHash);
    callback.searchParams.set("type", type);
    if (!callback.searchParams.has("next")) {
      callback.searchParams.set("next", pathname === "/" ? "/profil" : pathname);
    }
    return NextResponse.redirect(callback);
  }

  let response = NextResponse.next({ request });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return response;

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });

  await supabase.auth.getUser();
  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
