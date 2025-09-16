import React from "react";
import DashboardCard from "../components/DashboardCard";
import RecentActivityRow from "../components/RecentActivityRow";
import ReferralTrendsChart from "../components/ReferralTrendCharts";
import WithdrawalManagement from "../components/WithdrawalManagement";
import SimpleBar from "simplebar-react";
import { useUserContext } from "../context/UserProvider";

const Dashboard: React.FC = () => {
  const { user, loading } = useUserContext();

  return (
    <div className="sm:p-8 p-4 flex flex-col gap-8">
      {/* Top Section */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-500">
          Welcome Back 👋 <br />
          <span className="text-3xl font-semibold text-primary-blue">
            {loading ? "Loading..." : user?.name || "The Roof Co. Waco 👋"}
          </span>
        </h2>
        <div className="flex gap-3">{/* <Button text="Invite Team" /> */}</div>
      </div>

      {/* Dashboard Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <DashboardCard title="Referrals Created" value="125" change="+10%" />
        <DashboardCard title="Referrals Accepted" value="98" change="+5%" />
        <DashboardCard title="Referrals Completed" value="75" change="+8%" />
        <DashboardCard title="Total Points Allocated" value="$12,500" change="+3%" />
        <DashboardCard title="Points Cashed Value" value="$12,500" change="-5%" isNegative />
        <DashboardCard title="Missed Opportunity" value="$250" change="-5%" isNegative />
      </div>

      {/* Chart + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 lg:gap-6">
        {/* Chart */}
        <div className="col-span-2">
          <ReferralTrendsChart />
        </div>

        {/* Recent Activity */}
        <div className="bg-white p-6 rounded-xl shadow-sm md:mt-0 mt-6 flex flex-col">
          <h3 className="text-lg font-semibold text-primary-blue mb-6">Recent Activity</h3>

          {/* Make this scrollable */}
          <SimpleBar style={{ maxHeight: 450 }} autoHide={true}>
            <div className="space-y-6 pr-1">
              <RecentActivityRow text="New referral created by Sarah" time="2 hours ago" />
              <RecentActivityRow text="Referral accepted by David" time="2 hours ago" />
              <RecentActivityRow text="Referral completed by Emily" time="2 hours ago" />
              <RecentActivityRow text="New referral created by Sarah" time="2 hours ago" />
              <RecentActivityRow text="Referral accepted by David" time="2 hours ago" />
              <RecentActivityRow text="Referral completed by Emily" time="2 hours ago" />
              <RecentActivityRow text="New referral created by Sarah" time="2 hours ago" />
              <RecentActivityRow text="Referral accepted by David" time="2 hours ago" />
              <RecentActivityRow text="Referral completed by Emily" time="2 hours ago" />
            </div>
          </SimpleBar>
        </div>
      </div>

      <WithdrawalManagement />
    </div>
  );
};

export default Dashboard;
