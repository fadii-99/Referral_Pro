import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type TeamMember = {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: string;       // 🔥 ab string hai
  status: string;     // 🔥 ab string hai
  lastActive: string;
  phone?: string;
};

type Ctx = {
  loading: boolean;
  error: string | null;
  membersFromApi: TeamMember[];
  loadTeam: () => Promise<void>;
};


const TeamMembersContext = createContext<Ctx | null>(null);
export const useTeamMembersContext = () => {
  const ctx = useContext(TeamMembersContext);
  if (!ctx)
    throw new Error(
      "useTeamMembersContext must be used within <TeamMembersProvider>"
    );
  return ctx;
};

const serverUrl = import.meta.env.VITE_SERVER_URL;

export const TeamMembersProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [membersFromApi, setMembersFromApi] = useState<TeamMember[]>([]);

  const loadTeam = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("accessToken");

      const res = await fetch(`${serverUrl}/auth/employees/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: token ? `Bearer ${token}` : "",
          //  "ngrok-skip-browser-warning": "true", 
        },
      });

      
      if (!res.ok) {
        const errTxt = await res.text();
        console.error("[employee_list] error response:", errTxt);
        setError(`Failed (${res.status})`);
        setMembersFromApi([]);
        return;
      }

      const data = await res.json();
      console.log("[employee_list] full json:", data);

      const arr = Array.isArray(data?.employees) ? data.employees : [];
      console.log("[employee_list] employees array:", arr);

      const mapped: TeamMember[] = arr.map((emp: any) => ({
        id: String(emp.id),
        name: emp.full_name || "Unknown",
        email: emp.email,
        avatar: `https://i.pravatar.cc/96?u=${emp.email}`, // random avatar
        role: emp.role || "Unknown",                       // 🔥 directly string
        status: emp.is_active ? "Active" : "Inactive",     // 🔥 string
        lastActive: emp.last_login
          ? new Date(emp.last_login).toLocaleDateString()
          : "—",
        phone: emp.phone ?? "—",
      }));

      setMembersFromApi(mapped);
    } catch (err) {
      console.error("[employee_list] network error:", err);
      setError("Network error");
      setMembersFromApi([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTeam();
  }, [loadTeam]);

  const value = useMemo(
    () => ({ loading, error, membersFromApi, loadTeam }),
    [loading, error, membersFromApi, loadTeam]
  );

  return (
    <TeamMembersContext.Provider value={value}>
      {children}
    </TeamMembersContext.Provider>
  );
};
