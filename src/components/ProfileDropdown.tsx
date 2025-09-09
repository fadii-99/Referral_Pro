// src/components/ProfileDropdown.tsx
import React, { useEffect, useRef, useState } from "react";
import { FiSettings, FiCreditCard, FiLogOut } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

type ProfileDropdownProps = {
  name?: string;
  role?: string;
  avatarUrl?: string;
  className?: string;
};

const ProfileDropdown: React.FC<ProfileDropdownProps> = ({
  name = "Ansharah Rana",
  role = "Designer",
  avatarUrl = "https://i.pravatar.cc/160?img=12",
  className = "",
}) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close on outside click + Esc
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  // Row item
  const Item = ({ icon, label }: { icon: React.ReactNode; label: string }) => (
    <button
      type="button"
      onClick={(e) => e.preventDefault()} // read-only for now
      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-primary-purple/5 rounded-lg transition"
    >
      <span className="text-primary-purple text-lg">{icon}</span>
      <span className="text-xs font-medium text-[#0b0d3b]">{label}</span>
    </button>
  );

  const goProfile = () => {
    setOpen(false);
    navigate("/Dashboard/Profile");
  };

  return (
    <div className={`relative ${className}`} ref={ref}>
      {/* Avatar trigger */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="h-10 w-10 overflow-hidden rounded-full ring-2 ring-white shadow-sm border border-black/5"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Open profile menu"
      >
        <img src={avatarUrl} alt="User avatar" className="h-full w-full object-cover" />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-xl border border-black/5 p-4 z-50"
        >
          {/* Header */}
          <div className="flex items-center gap-3 px-2 border-b border-gray-100 pb-4">
            <img
              src={avatarUrl}
              alt=""
              className="h-16 w-auto rounded-full object-cover ring-2 ring-white shadow"
            />
            <div>
              <div className="font-semibold text-[#0b0d3b]">{name}</div>
              <div className="text-xs text-gray-500 pb-3">{role}</div>
              <button
                type="button"
                onClick={goProfile}
                className="text-xs text-primary-purple hover:underline"
              >
                View Profile
              </button>
            </div>
          </div>

          {/* Items */}
          <div className="space-y-1 pt-4">
            <Item icon={<FiSettings />} label="Setting" />
            <div className="h-px bg-gray-200 my-2" />
            <Item icon={<FiCreditCard />} label="Subscription & Billing" />
            <div className="h-px bg-gray-200 my-2" />
            <Item icon={<FiLogOut />} label="Logout" />
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileDropdown;
