import React from "react";

const data = Array.from({ length: 8 }, (_, i) => ({
  id: `a${i}`,
  title:
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit Aenean sit. Lorem ipsum dolor sit amet, consectetur adipiscing elit Aenean sit.",
  time: "10:35 PM",
}));

const Notifications: React.FC = () => {
  return (
    <div className="sm:p-6 p-3">
      {/* Header bar (title only – no search, no tabs) */}
        <h2 className="md:text-2xl text-xl font-semibold  text-primary-blue sm:pb-4 pb-0">Notifications</h2>

      {/* Card with list */}
      <div className="mt-4 bg-white rounded-2xl shadow-sm border border-black/5 p-4 sm:p-5">
        <ul className="space-y-3">
          {data.map((n) => (
            <li
              key={n.id}
              className="bg-white rounded-2xl border border-gray-200 px-4 py-3 sm:py-4 flex items-center gap-3"
            >
              <span className="h-9 w-9 rounded-xl bg-primary-purple/10 text-primary-purple grid place-items-center shrink-0">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <rect x="6" y="4" width="12" height="16" rx="2" />
                  <path d="M8 8h8M8 12h8M8 16h5" />
                </svg>
              </span>
              <div className="flex-1">
                <p className="md:text-sm text-xs text-primary-blue leading-snug">{n.title}</p>
              </div>
              <div className="sm:text-xs text-[10px] text-gray-400 shrink-0">{n.time}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Notifications;
