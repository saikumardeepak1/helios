"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getAccessToken } from "@/lib/api";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isChecked, setIsChecked] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    // Deferred to an effect deliberately: localStorage isn't available during
    // SSR, so checking synchronously would cause a hydration mismatch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsChecked(true);
  }, [router]);

  if (!isChecked) return null;

  return <>{children}</>;
}
