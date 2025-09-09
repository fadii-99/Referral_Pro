import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import referralProLogo from "./../assets/referralProLogo.png";
import NotificationDropdown from "../components/NotificationDropdown";
import ProfileDropdown from "../components/ProfileDropdown";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/Dashboard" },
  { label: "Analytics", href: "/Dashboard/Analytics" },
  { label: "Team", href: "/Dashboard/Team" },
  { label: "Referral", href: "/Dashboard/Referral" },
];

const Navbar: React.FC = () => {
  const [elevated, setElevated] = useState(false);

  useEffect(() => {
    const onScroll = () => setElevated(window.scrollY > 4);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={[
        "sticky top-0 z-50 border-b border-gray-300 bg-primary-gray transition-shadow",
        elevated ? "shadow-md" : "shadow-none",
      ].join(" ")}
    >
      <nav
        className="w-full px-4 sm:px-6 lg:px-8
                   grid grid-cols-[auto_1fr_auto] items-center gap-4 h-16"
      >
        {/* Left: Logo */}
        <div className="flex items-center gap-2">
          <img src={referralProLogo} alt="Referral Pro" className="h-6 w-auto" />
        </div>

        {/* Middle: Links */}
        <ul className="flex items-center justify-center gap-2 sm:gap-3">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <NavLink
                to={item.href}
                end={item.href.toLowerCase() === "/dashboard"}
                className={({ isActive }) =>
                  [
                    "px-4 py-2 rounded-full text-xs transition",
                    isActive
                      ? "text-primary-purple bg-primary-purple/15"
                      : "text-slate-600 hover:text-slate-800 hover:bg-slate-200/40",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          <NotificationDropdown />
          <ProfileDropdown />
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
