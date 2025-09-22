// src/context/UserProvider.tsx
import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";
// import { toast } from "react-toastify";

export type User = {
  id: string;
  name: string;
  type: "Admin" | "User";
  status: "Active" | "Inactive";
  registered: string;
  tenant: string;
};

type Ctx = {
  loading: boolean;
  error: string | null;
  users: User[];
  loadUsers: () => Promise<void>;
};

const AdminUserContext = createContext<Ctx | null>(null);

export const useAdminUserContext = () => {
  const ctx = useContext(AdminUserContext);
  if (!ctx) throw new Error("useAdminUserContext must be used inside provider");
  return ctx;
};

// 🚀 Dummy data (until API is ready)
const dummyUsers: User[] = [
  {
    id: "1",
    name: "John Smith",
    type: "Admin",
    status: "Inactive",
    registered: "01/01/2023",
    tenant: "Acme Corp",
  },
  {
    id: "2",
    name: "John Smith",
    type: "User",
    status: "Active",
    registered: "01/01/2023",
    tenant: "Acme Corp",
  },
  {
    id: "3",
    name: "John Smith",
    type: "Admin",
    status: "Active",
    registered: "01/01/2023",
    tenant: "Acme Corp",
  },
];

// const serverUrl = import.meta.env.VITE_SERVER_URL;

export const AdminUserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  const loadUsers = useCallback(async () => {
    // const token = localStorage.getItem("accessToken");
    // if (!token) return;

    setLoading(true);
    setError(null);

    try {
        const token = localStorage.getItem("adminToken");
    if (!token) return;
      // 👇 API call boilerplate (empty for now)
      const res = await fetch(``, {
        method: "GET",
        headers: {
          Accept: "application/json",
          // Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        // fallback to dummy
        setUsers(dummyUsers);
        return;
      }

      const data = await res.json();
      const arr = Array.isArray(data?.users) ? data.users : [];

      const mapped: User[] = arr.map((u: any) => ({
        id: String(u.id),
        name: u.name ?? "—",
        type: u.type ?? "User",
        status: u.status ?? "Inactive",
        registered: u.registered ?? "—",
        tenant: u.tenant ?? "—",
      }));

      setUsers(mapped.length > 0 ? mapped : dummyUsers);
    } catch (err: any) {
      // console.error("[user_list] error:", err);
      // toast.error("Failed to load users");
      setUsers(dummyUsers);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const value = useMemo(() => ({ loading, error, users, loadUsers }), [
    loading,
    error,
    users,
    loadUsers,
  ]);

  return <AdminUserContext.Provider value={value}>{children}</AdminUserContext.Provider>;
};
