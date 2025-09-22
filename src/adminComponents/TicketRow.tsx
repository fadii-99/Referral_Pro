// src/adminComponents/TicketRow.tsx
import React from "react";
import type { Ticket } from "../adminContext/AdminTicketProvider";

const Pill: React.FC<{ label: string; color: string }> = ({ label, color }) => (
  <span
    className={`inline-flex items-center w-fit px-3 py-1 rounded-lg text-xs sm:text-sm font-medium capitalize ${color}`}
  >
    {label}
  </span>
);

const TicketRow: React.FC<{ ticket: Ticket }> = ({ ticket }) => {
  const statusColor =
    ticket.status === "Open"
      ? "text-rose-700 bg-rose-50"
      : ticket.status === "Resolve"
      ? "text-emerald-700 bg-emerald-50"
      : "text-amber-700 bg-amber-50";

  return (
    <div
      className="grid grid-cols-[100px_150px_150px_150px_150px_150px_1fr] min-w-[900px]
                 items-center bg-white rounded-2xl px-6 py-3 border border-black/5 
                 shadow-sm hover:shadow-md transition"
    >
      <div className="font-medium text-gray-700">{ticket.id}</div>
      <div className="text-gray-700 font-medium">{ticket.user}</div>

      {/* Company with Logo */}
      <div className="flex items-center gap-2">
        <img src={ticket.companyLogo} alt={ticket.company} className="w-8 h-8 rounded-full" />
        <span className="text-gray-700 font-medium">{ticket.company}</span>
      </div>

      <div className="text-gray-600">{ticket.date}</div>
      <div className="text-gray-700">{ticket.agent}</div>
      <Pill label={ticket.status} color={statusColor} />
      <div className="text-gray-600">{ticket.summary}</div>
    </div>
  );
};


export default TicketRow;
