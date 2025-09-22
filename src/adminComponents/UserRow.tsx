// src/adminComponents/UserRow.tsx
import React from "react";
import type { User } from "./../adminContext/AdminUserProvider";

const Pill: React.FC<{ label: string; color: string }> = ({ label, color }) => (
  <span
    className={`inline-flex items-center w-fit px-3 py-1 rounded-lg text-nowrap text-xs sm:text-sm font-medium capitalize ${color}`}
  >
    {label}
  </span>
);

const UserRow: React.FC<{ user: User }> = ({ user }) => {
  const typeColor =
    user.type.toLowerCase() === "admin"
      ? "text-purple-700 bg-purple-50"
      : "text-blue-700 bg-blue-50";

  const statusColor =
    user.status.toLowerCase() === "active"
      ? "text-emerald-700 bg-emerald-50"
      : "text-amber-700 bg-amber-50";

  return (
    <div
      className="grid grid-cols-[1fr_1fr_1fr_1fr_1fr] min-w-[900px] 
                 items-center bg-white rounded-2xl px-6 py-3 border border-black/5 
                 shadow-sm hover:shadow-md transition"
    >
      {/* Name with avatar */}
      <div className="flex items-center gap-3 font-medium text-gray-700 md:text-sm text-xs">
        <img
          src={`https://ui-avatars.com/api/?name=${encodeURIComponent(
            user.name
          )}&background=0b0d3b&color=fff`}
          alt={user.name}
          className="w-8 h-8 rounded-full"
        />
        <span>{user.name}</span>
      </div>

      {/* User type */}
      <Pill label={user.type} color={typeColor} />

      {/* Activity status */}
      <Pill label={user.status} color={statusColor} />

      {/* Registration date */}
      <div className="text-gray-600 md:text-sm text-xs">{user.registered}</div>

      {/* Tenant */}
      <div className="font-medium text-gray-700 md:text-sm text-xs">
        {user.tenant}
      </div>
    </div>
  );
};

export default UserRow;
