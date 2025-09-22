// src/components/ReferralRow.tsx
import React from "react";
import { FiEye } from "react-icons/fi";

export type Referral = {
  id: string;
  reference_id: string;
  referred_to_name: string;
  industry: string; // 👈 Service Type
  assigned_to_name: string | null;
  status: string;
  urgency: string;
};

// 🎨 Available fallback colors (for unknown values)
const colors = [
  "text-rose-700 bg-rose-50",
  "text-blue-700 bg-blue-50",
  "text-amber-700 bg-amber-50",
  "text-emerald-700 bg-emerald-50",
  "text-purple-700 bg-purple-50",
  "text-gray-700 bg-gray-100",
];

const pickColor = (key: string) => {
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = key.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, string> = {
    pending: "text-amber-700 bg-amber-50",
    approved: "text-emerald-700 bg-emerald-50",
    closed: "text-rose-700 bg-rose-50",
  };
  const style = map[status.toLowerCase()] || pickColor(status);

  return (
    <span
      className={`inline-flex items-center w-fit px-3 py-1 rounded-lg text-nowrap text-xs sm:text-sm font-medium capitalize ${style}`}
    >
      {status}
    </span>
  );
};

const UrgencyPill: React.FC<{ urgency: string }> = ({ urgency }) => {
  const map: Record<string, string> = {
    urgent: "text-rose-700 bg-rose-50",
    normal: "text-blue-700 bg-blue-50",
    medium: "text-amber-700 bg-amber-50",
  };
  const style = map[urgency.toLowerCase()] || pickColor(urgency);

  return (
    <span
      className={`inline-flex items-center w-fit px-3 py-1 rounded-lg text-nowrap text-xs sm:text-sm font-medium capitalize ${style}`}
    >
      {urgency}
    </span>
  );
};

const ReferralRow: React.FC<{
  referral: Referral;
  onClick?: () => void;
  onView?: () => void;
}> = ({ referral, onClick, onView }) => {
  return (
    <div
      onClick={onClick}
      className="grid grid-cols-[160px_200px_1fr_1fr_1fr_1fr_60px] min-w-[900px] 
               items-center bg-white rounded-2xl px-6 py-3 border border-black/5 
               shadow-sm cursor-pointer hover:shadow-md transition"
    >
      {/* ID */}
      <div className="font-medium text-gray-700 md:text-sm text-xs text-left">
        {referral.reference_id}
      </div>

      {/* Customer Name */}
      <div className="font-medium text-gray-700 md:text-sm text-xs text-left">
        {referral.referred_to_name}
      </div>

      {/* Service Type */}
      <div className="text-gray-600 md:text-sm text-xs text-left">
        {referral.industry}
      </div>

      {/* Assigned Rep */}
      <div className="md:text-sm text-xs text-left">
        {referral.assigned_to_name ? (
          <span className="text-gray-700">{referral.assigned_to_name}</span>
        ) : (
          <span className="inline-flex items-center w-fit px-3 py-1 rounded-lg md:text-sm text-xs font-medium text-red-600 bg-red-50">
            none
          </span>
        )}
      </div>

      {/* Status */}
      <StatusPill status={referral.status} />

      {/* Priority */}
      <UrgencyPill urgency={referral.urgency} />

      {/* Actions */}
      <div className="flex justify-end pr-2" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          aria-label="View"
          className="text-primary-purple hover:opacity-80"
          onClick={onView}
        >
          <FiEye className="text-lg" />
        </button>
      </div>
    </div>
  );
};

export default ReferralRow;
