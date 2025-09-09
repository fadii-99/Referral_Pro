import React from "react";

export type Referral = {
  id: string;
  companyName: string;
  companyType: string;
  industry: string;
  status: string;
  urgency: string;
};

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, string> = {
    pending: "text-amber-700 bg-amber-50",
    approved: "text-emerald-700 bg-emerald-50",
    closed: "text-rose-700 bg-rose-50",
  };
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-lg text-xs sm:text-sm font-medium capitalize ${
        map[status.toLowerCase()] || "text-gray-700 bg-gray-50"
      }`}
    >
      {status}
    </span>
  );
};

const UrgencyPill: React.FC<{ urgency: string }> = ({ urgency }) => {
  const map: Record<string, string> = {
    urgent: "text-rose-700 bg-rose-50",
    normal: "text-blue-700 bg-blue-50",
    low: "text-slate-700 bg-slate-50",
  };
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-lg text-xs sm:text-sm font-medium capitalize ${
        map[urgency.toLowerCase()] || "text-gray-700 bg-gray-50"
      }`}
    >
      {urgency}
    </span>
  );
};


const ReferralRow: React.FC<{ referral: Referral }> = ({ referral }) => {
  return (
    <div className="grid grid-cols-[0.6fr_2fr_1.5fr_1.5fr_1.2fr_1fr] items-center bg-white rounded-2xl px-6 py-3 border border-black/5 shadow-sm">
      {/* ID */}
      <div className="font-medium text-gray-700 text-sm">{referral.id}</div>

      {/* Company Name */}
      <div className="font-medium text-gray-700 text-sm">
        {referral.companyName}
      </div>

      {/* Industry */}
      <div className="text-gray-600 text-sm">{referral.industry}</div>

      {/* Company Type */}
      <div className="text-gray-600 text-sm">{referral.companyType}</div>

      {/* Status */}
      <StatusPill status={referral.status} />

      {/* Urgency */}
      <UrgencyPill urgency={referral.urgency} />
    </div>
  );
};

export default ReferralRow;
