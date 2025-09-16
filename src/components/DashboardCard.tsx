import React from "react";

interface DashboardCardProps {
  title: string;
  value: string;
  change: string;
  isNegative?: boolean;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  change,
  isNegative = false,
}) => {
  return (
    <div className="bg-primary-blue text-white rounded-2xl sm:p-4 p-3 shadow-md relative">
      <h4 className="sm:text-sm text-xs">{title}</h4>
      <p className="sm:text-3xl text-2xl font-bold mt-2">{value}</p>
      <span
        className={`sm:text-sm text-xs ${
          isNegative ? "text-red-400" : "text-green-400"
        }`}
      >
        {change}
      </span>
      {/* <div className="absolute sm:top-5 top-2 sm:right-5 right-2 sm:w-[10px] sm:h-[10px] bg-secondary-blue rounded-full">
      </div> */}
    </div>
  );
};

export default DashboardCard;
