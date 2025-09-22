import React from "react";
import ForecastModelsChart from "./../adminComponents/ForecastModelsChart";
import RevenueSourcesChart from "./../adminComponents/RevenueSourcesChart";
import OutstandingBalances from "./../adminComponents/OutstandingBalances";
import WithdrawalManagement from "../components/WithdrawalManagement";



const AdminFinancial: React.FC = () => {
  return (
    <div className="sm:p-8 p-4 flex flex-col gap-8">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-semibold text-primary-blue">Financial Management</h2>
        <p className="text-gray-500 text-sm">Revenue Dashboard</p>
      </div>

      {/* Graphs Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ForecastModelsChart />
        <RevenueSourcesChart />
      </div>

      {/* Table */}
      <OutstandingBalances />
      <WithdrawalManagement />
    </div>
  );
};


export default AdminFinancial;
