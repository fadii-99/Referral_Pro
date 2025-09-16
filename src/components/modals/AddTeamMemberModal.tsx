import React, { useState } from "react";
import { FiX, FiUser, FiMail } from "react-icons/fi";
import Button from "../Button";
import { toast } from "react-toastify";
import { useTeamMembersContext } from "../../context/TeamMembersProvider";

const serverUrl = import.meta.env.VITE_SERVER_URL;

type Props = {
  open: boolean;
  onClose: () => void;
};

const AddTeamMemberModal: React.FC<Props> = ({ open, onClose }) => {
  const { loadTeam } = useTeamMembersContext();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const handleInvite = async () => {
    if (!name.trim() || !email.trim()) {
      toast.error("Name and Email are required!");
      return;
    }
    setLoading(true);
    try {
      const token = localStorage.getItem("accessToken");

      const fd = new FormData();
      fd.append("name", name.trim());
      fd.append("email", email.trim());

      const res = await fetch(`${serverUrl}/auth/employees/`, {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: fd,
      });

      const raw = await res.text();
      let data: any = null;
      try {
        data = raw ? JSON.parse(raw) : null;
      } catch {}

      if (!res.ok) {
        toast.error(data?.error || `Failed (${res.status})`);
        return;
      }

      // ✅ success
      toast.success("Invite sent successfully!");
      setName("");
      setEmail("");
      onClose();

      // 🔥 reload fresh team list
      await loadTeam();
    } catch (err) {
      console.error("[send-invite] error:", err);
      toast.error("Network error while sending invite.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-[1px] p-4">
      <div className="w-full max-w-xl bg-white rounded-3xl shadow-xl relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-6">
          <h3 className="text-2xl font-semibold text-primary-blue">
            Add Member
          </h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="h-8 w-8 rounded-full bg-white border border-black/5 shadow-sm grid place-items-center hover:shadow transition"
          >
            <FiX className="text-primary-purple" />
          </button>
        </div>

        {/* Form */}
        <div className="px-6 pb-6 space-y-5">
          {/* Name */}
          <div>
            <label className="block text-xs text-primary-blue font-medium mb-2">
              Name
            </label>
            <div className="relative">
              <span className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-purple">
                <FiUser className="h-5 w-5" />
              </span>
              <input
                type="text"
                placeholder="John Smith"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="block text-xs text-primary-blue font-medium mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-purple">
                <FiMail className="h-5 w-5" />
              </span>
              <input
                type="email"
                placeholder="email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>
          </div>

          {/* Submit */}
          <div className="pt-2">
            <Button
              text={loading ? "Sending..." : "Send Invite"}
              fullWidth
              py="py-5"
              mt="mt-0"
              onClick={handleInvite}
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddTeamMemberModal;
