import React from "react";
import AnalyticsPieChart from "../components/AnalyticsPieChart";
import ReferralTrendsChart from "../components/ReferralTrendCharts";


const Analytics: React.FC = () => {
  return (
        <div className="p-6 space-y-6 md:h-[calc(100vh-90px)] overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl md:text-2xl font-semibold text-primary-blue">
          Analytics Dashboard
        </h2>
       
      </div>

      {/* Grid takes rest of viewport */}
      <div className="grid md:grid-cols-5 grid-cols-1 md:gap-5 gap-0 h-full">
        <div className="col-span-2 h-full">
          <AnalyticsPieChart accepted={65} rejected={20} pending={15} className="h-full" />
        </div>
        <div className="col-span-3 h-full md:mt-0 mt-4 ">
          <ReferralTrendsChart />
        </div>
      </div>
    </div>

  );
};

export default Analytics;
