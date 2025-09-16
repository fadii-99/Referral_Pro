import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";

export type UserInfo = {
  id: string;
  name: string;
  email: string;
  role?: string;
  avatar?: string;
  phone?: string;
};

type Ctx = {
  loading: boolean;
  error: string | null;
  user: UserInfo | null;
  loadUser: () => Promise<void>;
};

const UserContext = createContext<Ctx | null>(null);

export const useUserContext = () => {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUserContext must be used within <UserProvider>");
  return ctx;
};


const serverUrl = import.meta.env.VITE_SERVER_URL;


export const UserProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);



  const loadUser = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("accessToken");
      if (!token) return;  
      const res = await fetch(`${serverUrl}/auth/get_user/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({}),
      });

      const data = await res.json();
      // console.log("[UserProvider] get_user response:", data);

      if (!res.ok) {
        setError(`Failed (${res.status})`);
        setUser(null);
        return;
      }
      
      const DEFAULT_AVATAR =
  "https://ui-avatars.com/api/?name=User&background=E5E7EB&color=374151"; 

      const mapped: UserInfo = {
        id: String(data?.user?.id || ""),
        name: data?.user?.full_name || "Unknown",
        email: data?.user?.email || "",
        phone: data?.user?.phone || "",
        role: data?.user?.role || "Member",
        avatar: data?.user?.image || DEFAULT_AVATAR,
      };

      setUser(mapped);
    } catch (err) {
      console.error("[UserProvider] network error:", err);
      setError("Network error");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  

  useEffect(() => {
    void loadUser();
  }, [loadUser]);


  const value = useMemo(
    () => ({ loading, error, user, loadUser }),
    [loading, error, user, loadUser]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};
