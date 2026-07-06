"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface NavLinkProps {
  href: string;
  children: ReactNode;
  icon: LucideIcon;
  onNavigate?: () => void;
}

export function NavLink({ href, children, icon: Icon, onNavigate }: NavLinkProps) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`flex items-center gap-3 border-l-[3px] px-4 py-2.5 text-[13px] transition md:justify-center md:px-0 lg:justify-start lg:px-4 ${
        active
          ? "border-transparent bg-[rgba(0,255,135,0.06)] text-fpl-green shadow-[inset_3px_0_0_#00FF87,0_0_12px_rgba(0,255,135,0.08)]"
          : "border-transparent text-primary hover:translate-x-0.5 hover:bg-[rgba(255,255,255,0.04)] hover:text-primary"
      }`}
      title={String(children)}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="md:hidden lg:inline">{children}</span>
    </Link>
  );
}
