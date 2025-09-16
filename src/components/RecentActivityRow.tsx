import React from "react";
import { FaUserCircle } from "react-icons/fa";

interface RecentActivityRowProps {
  text: string;
  time: string;
}

const RecentActivityRow: React.FC<RecentActivityRowProps> = ({ text, time }) => {
  return (
    <div className="flex items-start gap-3">
      <FaUserCircle className="text-primary-purple md:text-2xl text-xl mt-1" />
      <div className="flex flex-col items-start gap-1">
        <p className="md:text-sm text-xs text-gray-700">{text}</p>
        <span className="text-[10px] text-gray-400">{time}</span>
      </div>
    </div>
  );
};

export default RecentActivityRow;
