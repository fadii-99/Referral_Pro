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
    <div className="bg-primary-blue text-white rounded-2xl p-4 shadow-md relative">
      <h4 className="text-sm">{title}</h4>
      <p className="text-3xl font-bold mt-2">{value}</p>
      <span
        className={`text-sm ${
          isNegative ? "text-red-400" : "text-green-400"
        }`}
      >
        {change}
      </span>
      <div className="absolute top-5 right-5 w-[10px] h-[10px] bg-secondary-blue rounded-full">
      </div>
    </div>
  );
};

export default DashboardCard;
