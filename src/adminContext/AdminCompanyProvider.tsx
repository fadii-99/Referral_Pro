// src/adminContext/AdminCompanyProvider.tsx
import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";
// import { toast } from "react-toastify";

export type Company = {
  id: string;
  name: string;
  industry: string;
  status: "Compliant" | "Pending";
  plan: string;
  seat: string;
  payment: "Paid" | "Unpaid";
};

type Ctx = {
  loading: boolean;
  error: string | null;
  companies: Company[];
  loadCompanies: () => Promise<void>;
};

const AdminCompanyContext = createContext<Ctx | null>(null);

export const useAdminCompanyContext = () => {
  const ctx = useContext(AdminCompanyContext);
  if (!ctx) throw new Error("useAdminCompanyContext must be used inside provider");
  return ctx;
};

// 🚀 Dummy data
const dummyCompanies: Company[] = [
  {
    id: "1",
    name: "Global Solutions Ltd.",
    industry: "Technology",
    status: "Compliant",
    plan: "Enterprise",
    seat: "15/20",
    payment: "Unpaid",
  },
  {
    id: "2",
    name: "Global Solutions Ltd.",
    industry: "Technology",
    status: "Pending",
    plan: "Premium",
    seat: "15/20",
    payment: "Paid",
  },
  {
    id: "3",
    name: "Global Solutions Ltd.",
    industry: "Consulting",
    status: "Compliant",
    plan: "Basic",
    seat: "15/20",
    payment: "Paid",
  },
  {
    id: "4",
    name: "Global Solutions Ltd.",
    industry: "Manufacturing",
    status: "Pending",
    plan: "Enterprise",
    seat: "15/20",
    payment: "Unpaid",
  },
  {
    id: "5",
    name: "Global Solutions Ltd.",
    industry: "Technology",
    status: "Compliant",
    plan: "Enterprise",
    seat: "15/20",
    payment: "Unpaid",
  },
];

export const AdminCompanyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);

  const loadCompanies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("adminToken");
    if (!token) return;

      // 👇 API call boilerplate
      const res = await fetch(``);
      if (!res.ok) {
        setCompanies(dummyCompanies);
        return;
      }
      const data = await res.json();
      const arr = Array.isArray(data?.companies) ? data.companies : [];
      const mapped: Company[] = arr.map((c: any) => ({
        id: String(c.id),
        name: c.name ?? "—",
        industry: c.industry ?? "—",
        status: c.status ?? "Pending",
        plan: c.plan ?? "—",
        seat: c.seat ?? "—",
        payment: c.payment ?? "Unpaid",
      }));
      setCompanies(mapped.length > 0 ? mapped : dummyCompanies);
    } catch (err) {
      // console.error("[company_list] error:", err);
      // toast.error("Failed to load companies");
      setCompanies(dummyCompanies);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCompanies();
  }, [loadCompanies]);

  const value = useMemo(() => ({ loading, error, companies, loadCompanies }), [
    loading,
    error,
    companies,
    loadCompanies,
  ]);

  return <AdminCompanyContext.Provider value={value}>{children}</AdminCompanyContext.Provider>;
};
