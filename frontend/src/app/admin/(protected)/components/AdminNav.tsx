"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { LogOut } from "lucide-react";

const NAV_ITEMS = [
  { href: "/admin/dashboard", label: "대시보드" },
  { href: "/admin/packages", label: "패키지 관리" },
];

export function AdminNav() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <header className="border-b bg-primary text-primary-foreground">
      <div className="flex h-12 items-center justify-between px-4 md:px-8">
        <nav className="flex items-center gap-4">
          <span className="text-sm font-bold">관리자</span>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "text-sm transition-colors hover:text-accent",
                pathname === item.href
                  ? "font-semibold text-accent"
                  : "text-primary-foreground/70"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <Button
          variant="ghost"
          size="sm"
          onClick={logout}
          className="text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/10"
        >
          <LogOut className="size-4" />
          <span className="hidden sm:inline">로그아웃</span>
        </Button>
      </div>
    </header>
  );
}
