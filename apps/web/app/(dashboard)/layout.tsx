import { AuthGate } from "@/components/auth-gate";
import { Nav } from "@/components/nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <div className="grid min-h-screen grid-cols-[220px_1fr]">
        <Nav />
        <main className="p-8">{children}</main>
      </div>
    </AuthGate>
  );
}
