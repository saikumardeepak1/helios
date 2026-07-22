"use client";

import { AlertTriangle, Compass, DollarSign } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { clearTokens } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Traces", icon: Compass },
  { href: "/costs", label: "Costs", icon: DollarSign },
  { href: "/security", label: "Security", icon: AlertTriangle },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();

  function handleSignOut() {
    clearTokens();
    router.push("/login");
  }

  return (
    <nav className="flex h-full flex-col justify-between border-r border-slate-200 p-4">
      <div className="space-y-1">
        <p className="mb-4 px-2 text-lg font-semibold">Helios</p>
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium hover:bg-slate-100",
              pathname === href && "bg-slate-100"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </div>
      <Button variant="ghost" size="sm" onClick={handleSignOut}>
        Sign out
      </Button>
    </nav>
  );
}
