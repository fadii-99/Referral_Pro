import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";
import companyNameLogo from "./../assets/figmaIcons/companyName.png";
import IndustryLogo from "./../assets/figmaIcons/industry.png";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { RegistrationContext } from "../context/RegistrationProvider";

const INDUSTRIES = [
  "Technology",
  "Finance",
  "Healthcare",
  "Education",
  "Retail & E-commerce",
  "Manufacturing",
  "Logistics",
];

const BusinessRegistration: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("BusinessRegistration must be used within <RegistrationProvider>");
  const { registrationData, setRegistrationData } = ctx;

  const isCompany = registrationData.profileType === "company";

  // preload from context
  const [firstName, setFirstName]     = useState(registrationData.firstName || "");
  const [lastName, setLastName]       = useState(registrationData.lastName || "");
  const [email, setEmail]             = useState(registrationData.email || "");
  const [industry, setIndustry]       = useState(registrationData.industry || "");
  const [companyName, setCompanyName] = useState(registrationData.companyName || "");

  const [open, setOpen] = useState(false);

  useEffect(() => {
    setFirstName(registrationData.firstName || "");
    setLastName(registrationData.lastName || "");
    setEmail(registrationData.email || "");
    setIndustry(registrationData.industry || "");
    setCompanyName(registrationData.companyName || "");
  }, [registrationData]);

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    const missingBasics =
      !firstName.trim() || !lastName.trim() || !email.trim() || !industry.trim();
    const missingCompany = isCompany && !companyName.trim();

    if (missingBasics || missingCompany) {
      toast.error("Please fill out all fields.");
      return;
    }

    setRegistrationData(prev => ({
      ...prev,
      firstName: firstName.trim(),
      lastName : lastName.trim(),
      email    : email.trim(),
      industry : industry.trim(),
      companyName: isCompany ? companyName.trim() : "", // clear if not company
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
              total={7}
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
                      placeholder="Enter your first name"
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
                      placeholder="Enter your last name"
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
                    <img src={companyNameLogo} alt="" className="h-5 w-5 object-contain" />
                  </span>
                  <input
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                               text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Industry */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                  Industry Selection
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={IndustryLogo} alt="" className="h-5 w-5 object-contain" />
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
                    <ul className="absolute z-20 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg overflow-hidden">
                      {INDUSTRIES.map((opt) => (
                        <li key={opt}>
                          <button
                            type="button"
                            onClick={() => {
                              setIndustry(opt);
                              setOpen(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-primary-purple/5"
                            aria-selected={industry === opt}
                          >
                            {opt}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Company Name — only for company profile */}
              {isCompany && (
                <div>
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    Company Name
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <img src={companyNameLogo} alt="" className="h-5 w-5 object-contain" />
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
