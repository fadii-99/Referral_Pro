import React, { useEffect, useRef, useState } from "react";
import Button from "../Button";
import { FiX, FiUser, FiPhone, FiMail, FiCamera } from "react-icons/fi";
import { useUserContext } from "../../context/UserProvider";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const serverUrl = import.meta.env.VITE_SERVER_URL;

type Props = {
  open: boolean;
  onClose: () => void;
};

const EditProfileModal: React.FC<Props> = ({ open, onClose }) => {
  const { user, loadUser } = useUserContext();
  const [name, setName] = useState(user?.name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar || "");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const inputFileRef = useRef<HTMLInputElement | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName(user?.name || "");
    setPhone(user?.phone || "");
    setAvatarPreview(user?.avatar || "");
    setAvatarFile(null);
  }, [open, user]);

  if (!open) return null;

  const onPickFile = () => inputFileRef.current?.click();

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setAvatarFile(f);
    setAvatarPreview(URL.createObjectURL(f));
  };

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Name is required!");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("accessToken");

      const fd = new FormData();
      fd.append("full_name", name.trim());
      fd.append("phone", phone.trim());

      if (avatarFile) {
        fd.append("image", avatarFile);
      }

      const res = await fetch(`${serverUrl}/auth/update_user/`, {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: fd,
      });

      const data = await res.json();
      console.log("[update-user] response:", data);

      if (!res.ok) {
        toast.error(data?.error || `Failed (${res.status})`);
        return;
      }

      toast.success("Profile updated successfully!");
      await loadUser(); // ✅ Refresh context
      onClose();
    } catch (err) {
      console.error("[update-user] error:", err);
      toast.error("Network error while updating profile.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-[1px] p-4">
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6">
          <h3 className="text-2xl font-semibold text-primary-blue">
            Edit Profile
          </h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="h-8 w-8 rounded-full bg-white border border-black/5 shadow-sm grid place-items-center hover:shadow transition"
          >
            <FiX className="text-primary-purple" />
          </button>
        </div>

        {/* Avatar */}
        <div className="px-6 mt-3 flex flex-col items-center">
          <img
            src={avatarPreview}
            alt="avatar"
            className="h-24 w-24 rounded-full object-cover ring-2 ring-white shadow"
          />

          <button
            type="button"
            onClick={onPickFile}
            className="mt-2 inline-flex items-center gap-1 text-[11px] px-3 py-2 rounded-full bg-secondary-blue text-white font-light shadow"
          >
            <FiCamera className="text-white mr-1" />
            Change Photo
          </button>

          <input
            ref={inputFileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onFile}
          />
        </div>

        {/* Form */}
        <div className="px-6 pb-6 pt-4 space-y-5">
          {/* Name */}
          <div>
            <label className="block text-xs text-primary-blue font-medium mb-2">
              Full Name<span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-purple">
                <FiUser className="h-5 w-5" />
              </span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>
          </div>

          {/* Phone */}
          <div>
            <label className="block text-xs text-primary-blue font-medium mb-2">
              Phone
            </label>
            <div className="relative">
              <span className="absolute left-6 top-1/2 -translate-y-1/2 text-primary-purple">
                <FiPhone className="h-5 w-5" />
              </span>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>
          </div>

          {/* Email (locked) */}
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
                value={user?.email || ""}
                readOnly
                disabled
                className="w-full pl-14 pr-4 py-5 rounded-full bg-gray-50 border border-gray-200 text-xs text-gray-500 cursor-not-allowed"
              />
            </div>
          </div>

          {/* Save */}
          <div className="pt-2">
            <Button
              text={loading ? "Updating..." : "Update"}
              fullWidth
              py="py-5"
              mt="mt-0"
              onClick={handleSave}
              disabled={loading}
            />
          </div>
        </div>
      </div>

      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />
    </div>
  );
};

export default EditProfileModal;
