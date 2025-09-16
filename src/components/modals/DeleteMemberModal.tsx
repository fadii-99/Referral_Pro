// src/components/modals/DeleteMemberModal.tsx
import React, { useState } from "react";
import { FiX, FiTrash2 } from "react-icons/fi";
import Button from "../Button";
import type { TeamMember } from "../TeamRow";
import { useTeamMembersContext } from "../../context/TeamMembersProvider";

type Props = { open: boolean; member: TeamMember | null; onClose: () => void };
const serverUrl = import.meta.env.VITE_SERVER_URL;

const DeleteMemberModal: React.FC<Props> = ({ open, member, onClose }) => {
  const { loadTeam } = useTeamMembersContext();
  const [deleting, setDeleting] = useState(false);

  if (!open || !member) return null;

  const handleDelete = async () => {
    const token = localStorage.getItem("accessToken") || "";
    if (!serverUrl || !token) return;

    try {
      setDeleting(true);

      const res = await fetch(
        `${serverUrl}/auth/employees/?id=${encodeURIComponent(member.id)}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      if (!res.ok) {
        console.error("[DeleteMember] failed:", res.status, await res.text());
        return;
      }

      // ✅ refresh list + close
      await loadTeam();
      onClose();
    } catch (err) {
      console.error("[DeleteMember] error:", err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/30 backdrop-blur-[1px] p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl relative">
        <div className="flex items-center justify-between px-6 pt-6">
          <h3 className="text-xl font-semibold text-primary-blue">
            Delete Member
          </h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="h-8 w-8 rounded-full bg-white border grid place-items-center"
          >
            <FiX className="text-primary-purple" />
          </button>
        </div>

        <div className="px-6 pb-6 pt-4">
          <div className="flex items-start gap-3 py-3">
            <span className="h-10 w-10 rounded-xl bg-rose-50 text-rose-600 grid place-items-center">
              <FiTrash2 />
            </span>
            <p className="text-sm text-gray-700">
              Do you want to delete{" "}
              <span className="font-semibold text-[#0b0d3b]">
                {member.name}
              </span>
              ? This action cannot be undone.
            </p>
          </div>

          <div className="mt-6">
            <Button
              text={deleting ? "Deleting..." : "Delete"}
              fullWidth
              mt="mt-0"
              py="py-2 sm:py-3"
              className="bg-rose-500 text-white hover:opacity-95"
              onClick={handleDelete}
              disabled={deleting}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteMemberModal;
