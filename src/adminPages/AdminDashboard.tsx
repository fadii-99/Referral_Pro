import React from "react";
import DashboardCard from "../components/DashboardCard";
import UserTrendChart from "./../adminComponents/UserTrendChart";
import ReferralBreakdownChart from "./../adminComponents/ReferralBreakdownChart";


const AdminDashboard: React.FC = () => {
  return (
    <div className="sm:p-8 p-4 flex flex-col gap-8">
      {/* Top Section */}
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-medium text-gray-500">
          Admin Dashboard <br />
          <span className="text-3xl font-bold text-primary-blue">
            System Overview
          </span>
        </h2>
      </div>

      {/* Admin Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DashboardCard title="Active Users" value="12,345" change="+12%" />
        <DashboardCard title="Total Referrals" value="6,789" change="+8%" />
        <DashboardCard title="Revenue" value="$1,234,567" change="+15%" />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 lg:gap-6 gap-6">
        {/* User Trend Chart */}
        <UserTrendChart />

        {/* Referral Breakdown Chart */}
        <ReferralBreakdownChart />
      </div>


              {/* System Health Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm">
                <h3 className="sm:text-xl text-md font-semibold text-primary-blue mb-6">
                    System Health
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Card 1 */}
                    <div className="bg-[#f9f9ff] rounded-lg p-5 shadow-sm flex flex-col border">
                    <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-600">Total Points</h4>
                        <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                    </div>
                    <p className="text-2xl font-bold text-[#0b0d3b] mt-2">150,000</p>
                    <span className="text-sm text-red-500 mt-1">-10%</span>
                    </div>

                    {/* Card 2 */}
                    <div className="bg-[#f9f9ff] rounded-lg p-5 shadow-sm flex flex-col border">
                    <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-600">Total Cash Out</h4>
                        <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                    </div>
                    <p className="text-2xl font-bold text-[#0b0d3b] mt-2">$12,500</p>
                    <span className="text-sm text-red-500 mt-1">-5%</span>
                    </div>

                    {/* Card 3 */}
                    <div className="bg-[#f9f9ff] rounded-lg p-5 shadow-sm flex flex-col border">
                    <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-600">Total Active Subscription</h4>
                        <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                    </div>
                    <p className="text-2xl font-bold text-[#0b0d3b] mt-2">320</p>
                    <span className="text-sm text-green-500 mt-1">+1%</span>
                    </div>

                    {/* Card 4 */}
                    <div className="bg-[#f9f9ff] rounded-lg p-5 shadow-sm flex flex-col border">
                    <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-600">Cancelled Subscriptions</h4>
                        <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                    </div>
                    <p className="text-2xl font-bold text-[#0b0d3b] mt-2">45</p>
                    <span className="text-sm text-green-500 mt-1">+1%</span>
                    </div>
                </div>
                </div>

    </div>
  );
};


export default AdminDashboard;
