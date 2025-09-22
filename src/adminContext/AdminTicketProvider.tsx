// src/adminContext/AdminTicketProvider.tsx
import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";
// import { toast } from "react-toastify";

export type Ticket = {
  id: string;
  user: string;
  company: string;
  companyLogo: string;
  date: string;
  agent: string;
  status: "Open" | "Resolve" | "In progress";
  summary: string;
};

type Ctx = {
  loading: boolean;
  error: string | null;
  tickets: Ticket[];
  loadTickets: () => Promise<void>;
};

const AdminTicketContext = createContext<Ctx | null>(null);

export const useAdminTicketContext = () => {
  const ctx = useContext(AdminTicketContext);
  if (!ctx) throw new Error("useAdminTicketContext must be used inside provider");
  return ctx;
};

// 🚀 Dummy tickets
const dummyTickets: Ticket[] = [
  {
    id: "#12345",
    user: "Ethan Carter",
    company: "Keiser",
    companyLogo: "https://dummyimage.com/40x40/0b0d3b/fff.png&text=K", // 👈 dummy logo
    date: "2024-01-15",
    agent: "Liam Harper",
    status: "Open",
    summary: "Issue with login credentials",
  },
  {
    id: "#12346",
    user: "Ethan Carter",
    company: "Keiser",
    companyLogo: "https://dummyimage.com/40x40/0b0d3b/fff.png&text=K",
    date: "2024-01-15",
    agent: "Liam Harper",
    status: "Resolve",
    summary: "Payment processing error",
  },
  {
    id: "#12347",
    user: "Ethan Carter",
    company: "Keiser",
    companyLogo: "https://dummyimage.com/40x40/0b0d3b/fff.png&text=K",
    date: "2024-01-15",
    agent: "Liam Harper",
    status: "In progress",
    summary: "Server downtime issue",
  },
  {
    id: "#12348",
    user: "Ethan Carter",
    company: "Keiser",
    companyLogo: "https://dummyimage.com/40x40/0b0d3b/fff.png&text=K",
    date: "2024-01-15",
    agent: "Liam Harper",
    status: "Open",
    summary: "Issue with login credentials",
  },
  {
    id: "#12349",
    user: "Ethan Carter",
    company: "Keiser",
    companyLogo: "https://dummyimage.com/40x40/0b0d3b/fff.png&text=K",
    date: "2024-01-15",
    agent: "Liam Harper",
    status: "Open",
    summary: "Database connection issue",
  },
];

export const AdminTicketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
        const token = localStorage.getItem("adminToken");
    if (!token) return;
      const res = await fetch(``);
      if (!res.ok) {
        setTickets(dummyTickets);
        return;
      }
      const data = await res.json();
      const arr = Array.isArray(data?.tickets) ? data.tickets : [];
      const mapped: Ticket[] = arr.map((t: any) => ({
        id: String(t.id),
        user: t.user ?? "—",
        company: t.company ?? "—",
        companyLogo: t.companyLogo ?? "",
        date: t.date ?? "—",
        agent: t.agent ?? "—",
        status: t.status ?? "Open",
        summary: t.summary ?? "—",
      }));
      setTickets(mapped.length > 0 ? mapped : dummyTickets);
    } catch (err) {
      // console.error("[ticket_list] error:", err);
      // toast.error("Failed to load tickets");
      setTickets(dummyTickets);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const value = useMemo(() => ({ loading, error, tickets, loadTickets }), [
    loading,
    error,
    tickets,
    loadTickets,
  ]);

  return <AdminTicketContext.Provider value={value}>{children}</AdminTicketContext.Provider>;
};
