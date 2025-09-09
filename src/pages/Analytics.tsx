import React from "react";
import { FiSliders } from "react-icons/fi";
import AnalyticsPieChart from "../components/AnalyticsPieChart";
import ReferralTrendsChart from "../components/ReferralTrendCharts";

const Analytics: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl md:text-2xl font-semibold text-primary-blue">
          Analytics Dashboard
        </h2>
        <button
          type="button"
          aria-label="Filters"
          className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center hover:shadow transition"
        >
          <FiSliders className="text-primary-purple text-lg" />
        </button>
      </div>


       <div className="grid grid-cols-5 h-[calc(100vh-100px)] gap-5">
  <div className="col-span-2 h-full">
    <AnalyticsPieChart
      accepted={65}
      rejected={20}
      pending={15}
      className="h-full"
    />
  </div>
  <div className="col-span-3 h-full">
    <ReferralTrendsChart />
  </div>
</div>

      
    </div>
  );
};

export default Analytics;
