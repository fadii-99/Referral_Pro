// src/components/EditProfileModal/index.tsx (or your path)
import React, { useEffect, useRef, useState } from "react";
import Button from "./../Button";
import { FiX, FiUser, FiPhone, FiMail, FiCamera } from "react-icons/fi";
import type { ProfileData } from "./../../pages/Profile";

type Props = {
  open: boolean;
  profile: ProfileData;
  onClose: () => void;
  onSave: (p: ProfileData) => void;
};

const EditProfileModal: React.FC<Props> = ({ open, profile, onClose, onSave }) => {
  const [name, setName] = useState(profile.name);
  const [email, setEmail] = useState(profile.email);
  const [phone, setPhone] = useState(profile.phone);
  const [avatar, setAvatar] = useState(profile.avatar);

  const inputFileRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(profile.name);
    setEmail(profile.email);
    setPhone(profile.phone);
    setAvatar(profile.avatar);
  }, [open, profile]);

  if (!open) return null;

  const onPickFile = () => inputFileRef.current?.click();
  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") setAvatar(reader.result);
    };
    reader.readAsDataURL(f);
  };

  const handleSave = () => {
    onSave({ name: name.trim(), email: email.trim(), phone: phone.trim(), avatar });
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-[1px] p-4">
      <div className="w-full max-w-2xl bg-white rounded-3xl shadow-xl relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6">
          <h3 className="text-2xl font-semibold text-primary-blue">Edit Profile</h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="h-8 w-8 rounded-full bg-white border border-black/5 shadow-sm grid place-items-center hover:shadow transition"
          >
            <FiX className="text-primary-purple" />
          </button>
        </div>

        {/* Avatar + "Change Photo" */}
        <div className="px-6 mt-3 flex flex-col items-center">
          <img
            src={avatar}
            alt="avatar"
            className="h-24 w-24 rounded-full object-cover ring-2 ring-white shadow"
          />

          {/* Badge BELOW the image */}
          <button
            type="button"
            onClick={onPickFile}
            className="mt-2 inline-flex items-center gap-1 text-[11px] px-3 py-2 mt-1 rounded-full 
                       bg-secondary-blue text-white font-light shadow-[0_2px_10px_rgba(0,0,0,0.06)]"
          >
            <FiCamera className="text-white mr-1 " />
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
          {/* Full Name */}
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
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
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
                placeholder="Enter your phone number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
              />
            </div>
          </div>

          {/* Email (LOCKED) */}
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
                value={email}
                readOnly
                disabled
                aria-readonly
                className="w-full pl-14 pr-4 py-5 rounded-full bg-gray-50 border border-gray-200 
                           text-xs text-gray-500 placeholder-gray-400 outline-none cursor-not-allowed"
              />
            </div>
          </div>

          {/* Save */}
          <div className="pt-2">
            <Button text="Update" fullWidth py="py-5" mt="mt-0" onClick={handleSave} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditProfileModal;
