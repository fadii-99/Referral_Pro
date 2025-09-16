import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { HiOutlineMenu, HiX } from "react-icons/hi";
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
  const [menuOpen, setMenuOpen] = useState(false);

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
      <nav className="w-full px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Left: Logo + Mobile Hamburger */}
        <div className="flex items-center gap-3">
          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="md:hidden p-2 rounded-lg hover:bg-slate-200/40"
          >
            {menuOpen ? <HiX className="h-6 w-6" /> : <HiOutlineMenu className="h-6 w-6" />}
          </button>

          {/* Logo */}
          <img src={referralProLogo} alt="Referral Pro" className="h-6 w-auto" />
        </div>

        {/* Center: Desktop Links */}
        <ul className="hidden md:flex items-center gap-3">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <NavLink
                to={item.href}
                end={item.href.toLowerCase() === "/dashboard"}
                className={({ isActive }) =>
                  [
                    "px-4 py-2 rounded-full text-sm transition",
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

        {/* Right: Profile + Notification */}
        <div className="flex items-center gap-3">
          <NotificationDropdown />
          <ProfileDropdown />
        </div>
      </nav>

      {/* Mobile menu (links only) */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-gray-200 shadow-lg">
          <ul className="flex flex-col px-4 py-3 space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <NavLink
                  to={item.href}
                  end={item.href.toLowerCase() === "/dashboard"}
                  className={({ isActive }) =>
                    [
                      "block px-3 py-2 rounded-md text-sm font-medium",
                      isActive
                        ? "text-primary-purple bg-primary-purple/10"
                        : "text-slate-700 hover:bg-slate-100",
                    ].join(" ")
                  }
                  onClick={() => setMenuOpen(false)}
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      )}
    </header>
  );
};

export default Navbar;
