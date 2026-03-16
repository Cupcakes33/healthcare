import { PackageTable } from "./components/PackageTable";

export default function PackagesPage() {
  return (
    <div>
      <h1 className="mb-6 text-xl font-bold text-primary">패키지 관리</h1>
      <PackageTable />
    </div>
  );
}
