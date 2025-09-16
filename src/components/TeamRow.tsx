import React from "react";
import { FiEdit2, FiTrash2 } from "react-icons/fi";

export type TeamMember = {
  id: string;
  name: string;
  avatar: string;
  role: string;
  status: string;
  email: string;
  phone?: string;
  lastActive?: string;
};

const RolePill: React.FC<{ role: string }> = ({ role }) => (
  <span className="inline-flex items-center px-3 py-2 rounded-lg md:text-sm text-xs font-medium text-primary-purple bg-primary-purple/10">
    {role}
  </span>
);

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, string> = {
    Active: "text-emerald-700 bg-emerald-100",
    Inactive: "text-rose-700 bg-rose-100",
    Pending: "text-amber-700 bg-amber-100",
  };
  const classes = map[status] || "text-gray-700 bg-gray-100";

  return (
    <span
      className={`inline-flex items-center px-3 py-2 rounded-lg md:text-sm text-xs font-medium ${classes}`}
    >
      {status}
    </span>
  );
};

const TeamRow: React.FC<{
  member: TeamMember;
  onEdit?: (m: TeamMember) => void;
  onDelete?: (m: TeamMember) => void;
}> = ({ member, onEdit, onDelete }) => {
  return (
    <div className="grid grid-cols-[0.6fr_2fr_1.8fr_1.2fr_1.2fr_1fr] min-w-[650px] items-center bg-white rounded-2xl md:px-6 px-3 py-3 border border-black/5 shadow-sm">
      {/* ID */}
      <div className="font-medium text-gray-700 md:text-sm text-xs">
        {member.id}
      </div>

      {/* Name + Avatar */}
      <div className="flex items-center gap-3">
        <img
          src={member.avatar}
          alt={`${member.name} avatar`}
          className="h-8 w-8 rounded-full object-cover"
        />
        <span className="font-medium text-gray-700 md:text-sm text-xs">
          {member.name}
        </span>
      </div>

      {/* Email */}
      <div className="text-gray-600 md:text-sm text-xs pr-2">
        {member.email}
      </div>

      {/* Role */}
      <div>
        <RolePill role={member.role} />
      </div>

      {/* Status */}
      <div>
        <StatusPill status={member.status} />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-4 pr-3">
        <button
          type="button"
          className="text-primary-purple hover:opacity-80"
          aria-label="Edit"
          onClick={() => onEdit?.(member)}
        >
          <FiEdit2 />
        </button>
        <button
          type="button"
          className="text-primary-purple hover:opacity-80"
          aria-label="Delete"
          onClick={() => onDelete?.(member)}
        >
          <FiTrash2 />
        </button>
      </div>
    </div>
  );
};

export default TeamRow;
