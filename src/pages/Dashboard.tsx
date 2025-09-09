import React, { useEffect, useState } from "react";
import DashboardCard from "../components/DashboardCard";
import RecentActivityRow from "../components/RecentActivityRow";
import ReferralTrendsChart from "../components/ReferralTrendCharts";

const serverUrl = import.meta.env.VITE_SERVER_URL;

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);



useEffect(() => {
  const fetchUser = async () => {
    try {
      const token = localStorage.getItem("accessToken");

      const res = await fetch(`${serverUrl}/auth/get_user/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({}),
      });

      const json = await res.json();
      console.log("[get-user] response:", json); // ✅ sirf yeh dikhayega

      if (res.ok) {
        setUser(json);
      }
    } catch (err) {
      console.error("[get-user] error:", err);
    } finally {
      setLoading(false);
    }
  };

  fetchUser();
}, []);



  return (
    <div className="p-8 flex flex-col gap-8">
      {/* Top Section */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-500">
          Welcome Back 👋 <br />
          <span className="text-3xl font-semibold text-primary-blue">
            {loading ? "Loading..." : user?.user?.name || "The Roof Co. Waco 👋"}
          </span>
        </h2>
        <div className="flex gap-3">{/* <Button text="Invite Team" /> */}</div>
      </div>

      {/* Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <DashboardCard title="Referrals Created" value="125" change="+10%" />
        <DashboardCard title="Referrals Accepted" value="98" change="+5%" />
        <DashboardCard title="Referrals Completed" value="75" change="+8%" />
        <DashboardCard title="Total Points Allocated" value="$12,500" change="+3%" />
        <DashboardCard title="Points Cashed Value" value="$12,500" change="-5%" isNegative />
        <DashboardCard title="Missed Opportunity" value="$250" change="-5%" isNegative />
      </div>

      {/* Chart + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="col-span-2">
          <ReferralTrendsChart />
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            <RecentActivityRow text="New referral created by Sarah" time="2 hours ago" />
            <RecentActivityRow text="Referral accepted by David" time="2 hours ago" />
            <RecentActivityRow text="Referral completed by Emily" time="2 hours ago" />
            <RecentActivityRow text="Referral completed by Emily" time="2 hours ago" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
