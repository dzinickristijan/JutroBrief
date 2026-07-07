"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface Props {
  userEmail: string | null;
}

export function HeaderNav({ userEmail }: Props) {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path;

  return (
    <header className="site-header">
      <Link href="/" className="block">
        <h1 className="site-header__title">
          Jutarnji brief<span className="site-header__dot">.</span>
        </h1>
        <p className="site-header__tagline">
          Sve što je bitno iz Hrvatske i svijeta — u 5 minuta, svako jutro.
        </p>
      </Link>
      <nav className="site-nav">
        <Link href="/" className={isActive("/") ? "site-nav__active" : ""}>
          Početna
        </Link>
        <Link href="/arhiva" className={isActive("/arhiva") ? "site-nav__active" : ""}>
          Arhiva
        </Link>
        {userEmail ? (
          <Link href="/profil" className={isActive("/profil") ? "site-nav__active" : ""}>
            Profil
          </Link>
        ) : (
          <Link href="/prijava" className={isActive("/prijava") ? "site-nav__active" : ""}>
            Prijava
          </Link>
        )}
      </nav>
    </header>
  );
}
