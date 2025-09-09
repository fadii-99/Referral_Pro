import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { Referral } from "../components/ReferralRow";

type Ctx = {
  loading: boolean;
  error: string | null;
  referrals: Referral[];
  loadReferrals: () => Promise<void>;
};

const ReferralContext = createContext<Ctx | null>(null);

export const useReferralContext = () => {
  const ctx = useContext(ReferralContext);
  if (!ctx) throw new Error("useReferralContext must be used inside provider");
  return ctx;
};

const serverUrl = import.meta.env.VITE_SERVER_URL;

export const ReferralProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);

  const loadReferrals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("accessToken");

      const res = await fetch(`${serverUrl}/refer/list_company_referral/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
      });

      
      if (!res.ok) {
        const errTxt = await res.text();
        console.error("[referrals_list] error response:", errTxt);
        setError(`Failed (${res.status})`);
        setReferrals([]);
        return;
      }

      const data = await res.json();
      console.log("[referrals_list] full json:", data);

      const arr = Array.isArray(data) ? data : Array.isArray(data?.referrals) ? data.referrals : [];
      console.log("[referrals_list] extracted array:", arr);

      const mapped: Referral[] = arr.map((r: any) => ({
        id: String(r.id),
        companyName: r.company_name ?? "Unknown",
        companyType: r.company_type ?? "—",
        industry: r.industry ?? "—",
        status: r.status ?? "pending",
        urgency: r.urgency ?? "normal",
      }));

      setReferrals(mapped);
    } catch (err) {
      console.error("[referrals_list] network error:", err);
      setError("Network error");
      setReferrals([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReferrals();
  }, [loadReferrals]);

  const value = useMemo(
    () => ({ loading, error, referrals, loadReferrals }),
    [loading, error, referrals, loadReferrals]
  );

  return (
    <ReferralContext.Provider value={value}>
      {children}
    </ReferralContext.Provider>
  );
};
