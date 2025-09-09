import React, { useEffect, useRef, useState } from "react";
import { HiOutlineBell } from "react-icons/hi";
import { useNavigate } from "react-router-dom";

type Notif = {
  id: string;
  title: string;
  time: string; // e.g., "10:35 PM"
};

const DUMMY: Notif[] = [
  { id: "n1", title: "Lorem ipsum dolor sit amet, consectetur adipiscing elit Aenean sit", time: "10:35 PM" },
  { id: "n2", title: "New referral created by Sarah", time: "10:35 PM" },
  { id: "n3", title: "Referral accepted by David", time: "10:35 PM" },
  { id: "n4", title: "Referral completed by Emily", time: "10:35 PM" },
];

const NotificationDropdown: React.FC = () => {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close on outside click / escape
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const goAll = () => {
    setOpen(false);
    navigate("/Dashboard/Notifications"); // <-- view-all page route
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger — active (open) => bg-primary-blue + white icon */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={[
          "h-10 w-10 rounded-2xl border border-black/5 flex items-center justify-center transition shadow-sm",
          open ? "bg-primary-blue text-white hover:opacity-95" : "bg-white hover:shadow",
        ].join(" ")}
        aria-label="Notifications"
        aria-expanded={open}
      >
        <HiOutlineBell className={open ? "text-white text-xl" : "text-primary-purple text-xl"} />
      </button>

      {/* unread dot */}
      <span
        className={[
          "absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full ring-2",
          "bg-red-500",
          // ring should match navbar bg (primary-gray). adjust if different.
          "ring-[#f3f2fa]",
        ].join(" ")}
      />

      {/* Panel */}
      {open && (
        <div
          className="absolute right-0 mt-3 w-[22rem] bg-white border border-gray-200 rounded-2xl shadow-xl z-50 overflow-hidden"
          role="dialog"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
            <h4 className="text-lg font-semibold text-[#0b0d3b]">Notifications</h4>
            <button
              type="button"
              onClick={goAll}
              className="text-primary-purple text-xs font-medium hover:underline hover:underline-offset-4"
            >
              View All
            </button>
          </div>

          {/* List */}
          <ul className="divide-y divide-gray-200">
            {DUMMY.slice(0, 4).map((n) => (
              <li key={n.id} className="px-5 py-4 flex items-start gap-3">
                <span className="h-9 w-9 rounded-xl bg-primary-purple/10 text-primary-purple grid place-items-center shrink-0">
                  {/* tiny doc icon look */}
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <rect x="6" y="4" width="12" height="16" rx="2" />
                    <path d="M8 8h8M8 12h8M8 16h5" />
                  </svg>
                </span>
                <div className="flex-1">
                  <p className="text-[13px] text-[#0b0d3b] leading-snug">
                    {n.title}
                  </p>
                  <div className="text-[11px] text-gray-400 mt-2">{n.time}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown;
