// src/adminComponents/CompanyRow.tsx
import React from "react";
import type { Company } from "../adminContext/AdminCompanyProvider";

const Pill: React.FC<{ label: string; color: string }> = ({ label, color }) => (
  <span
    className={`inline-flex items-center w-fit px-3 py-1 rounded-lg text-xs sm:text-sm font-medium capitalize ${color}`}
  >
    {label}
  </span>
);

const CompanyRow: React.FC<{ company: Company }> = ({ company }) => {
  const statusColor =
    company.status === "Compliant"
      ? "text-purple-700 bg-purple-50"
      : "text-amber-700 bg-amber-50";

  const paymentColor =
    company.payment === "Paid"
      ? "text-emerald-700 bg-emerald-50"
      : "text-rose-700 bg-rose-50";

  return (
    <div
      className="grid grid-cols-[200px_150px_150px_150px_150px_150px_100px] min-w-[900px]
                 items-center bg-white rounded-2xl px-6 py-3 border border-black/5 
                 shadow-sm hover:shadow-md transition"
    >
      <div className="font-medium text-gray-700">{company.name}</div>
      <div className="text-blue-600 font-medium">{company.industry}</div>
      <Pill label={company.status} color={statusColor} />
      <div className="text-gray-600">{company.plan}</div>
      <div className="text-gray-600">{company.seat}</div>
      <Pill label={company.payment} color={paymentColor} />
      <button className="text-primary-purple hover:underline">Deactivate</button>
    </div>
  );
};

export default CompanyRow;
