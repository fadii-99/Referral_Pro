import React, { useEffect, useState } from "react";
import { FiX, FiUser } from "react-icons/fi";
import Button from "../Button";
import type { TeamMember } from "../TeamRow";

type Props = {
  open: boolean;
  member: TeamMember | null;
  onClose: () => void;
  onSave: () => void; // parent se loadTeam call hoga
};

const serverUrl = import.meta.env.VITE_SERVER_URL;

const EditTeamMemberModal: React.FC<Props> = ({ open, member, onClose, onSave }) => {
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && member) {
      setName(member.name ?? "");
      setSaving(false);
    }
  }, [open, member]);

  if (!open || !member) return null;

  const handleUpdate = async () => {
    const token = localStorage.getItem("accessToken") || "";
    if (!serverUrl || !token) return;

    try {
      setSaving(true);

      // 👇 form-data banaya
      const formData = new FormData();
      formData.append("id", member.id);       // 👈 id
      formData.append("name", name.trim());   // 👈 updated name

      const res = await fetch(`${serverUrl}/auth/employees/`, {
        method: "PUT", // ya POST agar backend POST expect kare
        headers: {
          Authorization: `Bearer ${token}`,
          // ❌ Content-Type set nahi karna — browser FormData ke sath khud karega
        },
        body: formData,
      });

      if (!res.ok) {
        console.error("[EditMember] PUT failed:", res.status, await res.text());
        setSaving(false);
        return;
      }

      onClose();
      await onSave();
    } catch (err) {
      console.error("[EditMember] PUT error:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-6">
          <h3 className="text-xl font-semibold text-primary-blue">Edit Member</h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="h-8 w-8 rounded-full border grid place-items-center hover:bg-gray-100"
          >
            <FiX className="text-primary-purple" />
          </button>
        </div>

        {/* Name input only */}
        <div className="px-6 pb-6 space-y-5">
          <div>
            <label className="block text-xs text-primary-blue font-medium mb-2">Name</label>
            <div className="relative">
              <span className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-purple">
                <FiUser className="h-5 w-5" />
              </span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter name"
                className="w-full pl-14 pr-4 py-4 rounded-full border text-sm text-gray-800 outline-none focus:ring-2 focus:ring-primary-blue/20"
              />
            </div>
          </div>

          <Button
            text={saving ? "Updating..." : "Update"}
            fullWidth
            py="py-4"
            mt="mt-0"
            onClick={handleUpdate}
            disabled={saving || !name.trim()}
          />
        </div>
      </div>
    </div>
  );
};

export default EditTeamMemberModal;
