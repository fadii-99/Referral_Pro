import React from "react";
import { FaUserCircle } from "react-icons/fa";

interface RecentActivityRowProps {
  text: string;
  time: string;
}

const RecentActivityRow: React.FC<RecentActivityRowProps> = ({ text, time }) => {
  return (
    <div className="flex items-start gap-3">
      <FaUserCircle className="text-primary-purple text-2xl" />
      <div>
        <p className="text-sm text-slate-800">{text}</p>
        <span className="text-xs text-slate-500">{time}</span>
      </div>
    </div>
  );
};

export default RecentActivityRow;
