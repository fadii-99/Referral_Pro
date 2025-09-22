import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";
import companyNameLogo from "./../assets/figmaIcons/companyName.png";
import messageIcon from "../assets/figmaIcons/sms.svg";
import IndustryLogo from "./../assets/figmaIcons/industry.png";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { RegistrationContext } from "../context/RegistrationProvider";
import { categories } from "./Category";

const BusinessRegistration: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("BusinessRegistration must be used within <RegistrationProvider>");
  const { registrationData, setRegistrationData } = ctx;

  const isCompany = registrationData.profileType === "company";

  // preload from context
  const [firstName, setFirstName] = useState(registrationData.firstName || "");
  const [lastName, setLastName] = useState(registrationData.lastName || "");
  const [email, setEmail] = useState(registrationData.email || "");
  const [industry, setIndustry] = useState(registrationData.industry || "");
  const [companyName, setCompanyName] = useState(registrationData.companyName || "");
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  // ✅ Normalize helper
  const normalize = (str: string) =>
    str.trim().toLowerCase().replace(/–/g, "-");

  // ✅ Flatten + deduplicate subcategories
  const SUBCATEGORIES = Array.from(
    new Map(
      categories
        .flatMap(cat =>
          cat.subcategories.map(sub => ({
            subcategory: sub.trim(),
            icon: cat.icon,
          }))
        )
        .map(item => [item.subcategory.toLowerCase(), item]) // unique by lowercase
    ).values()
  ).sort((a, b) => a.subcategory.localeCompare(b.subcategory));

  // ✅ Progressive strict search
  const normalizedSearch = normalize(search);
  const filtered = SUBCATEGORIES.filter(sub =>
    !normalizedSearch
      ? true
      : normalize(sub.subcategory).startsWith(normalizedSearch)
  );

  useEffect(() => {
    setFirstName(registrationData.firstName || "");
    setLastName(registrationData.lastName || "");
    setEmail(registrationData.email || "");
    setIndustry(registrationData.industry || "");
    setCompanyName(registrationData.companyName || "");
  }, [registrationData]);

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.(com|org|net|edu|gov|mil|info|biz|xyz|online)(\.[a-z]{2,})?$/i;
    const nameRegex = /^[A-Za-z]+$/;

    if (!nameRegex.test(firstName.trim())) {
      toast.error("First name should contain only letters without spaces.");
      return;
    }
    if (!nameRegex.test(lastName.trim())) {
      toast.error("Last name should contain only letters without spaces.");
      return;
    }

    const missingBasics =
      !firstName.trim() || !lastName.trim() || !email.trim() || !industry.trim();
    const missingCompany = isCompany && !companyName.trim();

    if (missingBasics || missingCompany) {
      toast.error("Please fill out all fields.");
      return;
    }

    if (!emailRegex.test(email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setRegistrationData(prev => ({
      ...prev,
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      email: email.trim(),
      industry: industry.trim(),
      companyName: isCompany ? companyName.trim() : "",
    }));

    navigate("/BusinessType");
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Business Registration"
              current={1}
              total={6}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            <div className="space-y-4">
              {/* First Name */}
              <div className="flex flex-row items-center justify-between gap-4 w-full">
                <div className="w-full">
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    First Name
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <img src={companyNameLogo} alt="" className="h-5 w-5 object-contain" />
                    </span>
                    <input
                      type="text"
                      placeholder="Enter first name"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                                text-gray-800 placeholder-gray-400 outline-none"
                    />
                  </div>
                </div>

                {/* Last Name */}
                <div className="w-full">
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    Last Name
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <img src={companyNameLogo} alt="" className="h-5 w-5 object-contain" />
                    </span>
                    <input
                      type="text"
                      placeholder="Enter last name"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                                text-gray-800 placeholder-gray-400 outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                  Email
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={messageIcon} alt="" className="h-5 w-5 object-contain" />
                  </span>
                  <input
                    type="email"
                    required
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                               text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Industry Selection */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                  Industry Selection
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    {industry ? (
                      <img
                        src={SUBCATEGORIES.find((s) => s.subcategory === industry)?.icon || IndustryLogo}
                        alt=""
                        className="h-5 w-5 object-contain"
                      />
                    ) : (
                      <img src={IndustryLogo} alt="" className="h-5 w-5 object-contain" />
                    )}
                  </span>

                  <button
                    type="button"
                    onClick={() => setOpen((s) => !s)}
                    className="w-full pl-12 pr-10 py-4 rounded-full bg-white border border-gray-200 text-left
                               text-xs md:text-sm text-gray-800 outline-none"
                  >
                    {industry || "Select your industry"}
                  </button>

                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>

                  {open && (
                    <div
                      className="absolute z-30 mt-2 w-full bg-white border border-gray-200 
                                 rounded-2xl shadow-lg overflow-auto 
                                 max-h-56 text-[11px] sm:text-sm"
                    >
                      {/* Search input */}
                      <div className="sticky top-0 bg-white border-b border-gray-200 p-2">
                       <input
                          type="text"
                          value={search}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (/^[a-zA-Z\s]*$/.test(val)) {
                              setSearch(val);
                            }
                          }}
                          placeholder="Search an industry..."
                          className="w-full px-3 py-2 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                                    text-gray-800 placeholder-gray-400 outline-none"
                        />

                      </div>

                      <ul>
                        {filtered.length > 0 ? (
                          filtered.map((opt) => (
                            <li key={opt.subcategory}>
                              <button
                                type="button"
                                onClick={() => {
                                  setIndustry(opt.subcategory);
                                  setOpen(false);
                                  setSearch("");
                                }}
                                className={`w-full flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 
                                          hover:bg-primary-purple/10 ${
                                            industry === opt.subcategory ? "bg-primary-purple/20" : ""
                                          }`}
                                aria-selected={industry === opt.subcategory}
                              >
                                <span className="text-xs sm:text-sm">{opt.subcategory}</span>
                              </button>
                            </li>
                          ))
                        ) : (
                          <li className="px-4 py-2 text-gray-400 text-xs sm:text-sm">
                            No such category found
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Company Name */}
              {isCompany && (
                <div>
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    Company Name
                  </label>
                  <div className="relative">
                   <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5 text-primary-purple"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3 21V9a2 2 0 012-2h2V5a2 2 0 012-2h6a2 2 0 012 2v2h2a2 2 0 012 2v12M9 21V9m6 12V9M3 21h18"
                        />
                      </svg>
                    </span>
                    <input
                      type="text"
                      placeholder="Enter company name"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                                 text-gray-800 placeholder-gray-400 outline-none"
                    />
                  </div>
                </div>
              )}
            </div>

            <Button text="Business Type Selection" onClick={handleContinue} />
          </div>
        </div>
      </div>

      <ToastContainer
        position="top-right"
        autoClose={2000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        pauseOnHover
        draggable
      />
    </div>
  );
};

export default BusinessRegistration;
