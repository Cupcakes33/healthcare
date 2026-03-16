import { AdminGuard } from "@/components/AdminGuard";
import { AdminNav } from "./components/AdminNav";

export default function AdminProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGuard>
      <div className="min-h-screen bg-background">
        <AdminNav />
        <main className="px-4 py-6 md:px-8">{children}</main>
      </div>
    </AdminGuard>
  );
}
