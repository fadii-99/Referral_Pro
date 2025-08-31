import React, { useState, useEffect, useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { RegistrationContext, type BizType } from "./../context/RegistrationProvider";

const YEARS_OPTIONS = [
  "Less than 1 year",
  "1 – 2 years",
  "3 – 5 years",
  "6 – 10 years",
  "10+ years",
];

const EMPLOYEE_OPTIONS = ["1 – 50", "51 – 100", "100 – 500", "500+"];

const US_STATES = [
  "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
  "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky",
  "Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi",
  "Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico",
  "New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
  "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
  "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
];

const BusinessType: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("BusinessType must be used within <RegistrationProvider>");
  const { registrationData, setRegistrationData } = ctx;

  const isContractor = registrationData.profileType === "contractor";
  const isCompany    = registrationData.profileType === "company";

  const TOTAL_STEPS = useMemo(() => (isCompany ? 6 : 4), [isCompany]);

  const [type, setType] = useState<BizType>(registrationData.bizType);
  const [years, setYears] = useState(registrationData.years);
  const [employees, setEmployees] = useState(registrationData.employees);
  const [usState, setUsState] = useState<string>(registrationData.usState);

  const [openYears, setOpenYears] = useState(false);
  const [openEmp, setOpenEmp] = useState(false);
  const [openState, setOpenState] = useState(false);

  const [loading] = useState(false);

  useEffect(() => {
    if (isContractor && type !== "sole") {
      setType("sole");
      setRegistrationData((prev) => ({ ...prev, bizType: "sole" }));
    }
  }, [isContractor, type, setRegistrationData]);

  useEffect(() => {
    setType(registrationData.bizType);
    setYears(registrationData.years);
    setEmployees(registrationData.employees);
    setUsState(registrationData.usState);
  }, [
    registrationData.bizType,
    registrationData.years,
    registrationData.employees,
    registrationData.usState,
  ]);

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (!years.trim() || !employees.trim()) {
      toast.error("Please fill out all fields.");
      return;
    }

    // Guard again here so payload is always correct
    const nextType: BizType = isContractor ? "sole" : type;

    setRegistrationData((prev) => ({
      ...prev,
      bizType: nextType,
      years: years.trim(),
      employees: employees.trim(),
      usState: usState?.trim() || "",
    }));

    navigate("/CompanyInformation");
  };

  const TypeCard: React.FC<{ value: BizType; label: string }> = ({ value, label }) => {
    const active = type === value;
    const disabled = isContractor; // lock for contractor

    return (
      <button
        type="button"
        onClick={() => !disabled && setType(value)}
        className={`relative w-full rounded-3xl sm:p-6 p-3 text-left bg-white border
                    shadow-[0_6px_24px_rgba(0,0,0,0.06)] transition
                    hover:shadow-[0_8px_28px_rgba(0,0,0,0.10)]
                    ${active ? "border-primary-purple/60" : "border-gray-200"}
                    ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
        aria-pressed={active}
        aria-disabled={disabled}
      >
        <span className="block sm:text-[13px] text-xs font-semibold text-primary-blue">
          {label}
        </span>

        <span
          className={`absolute right-3 top-3 h-5 w-5 rounded-full border flex items-center justify-center
                      ${active ? "border-primary-purple" : "border-gray-300"}`}
          aria-label={active ? "Selected" : "Not selected"}
        >
          <span
            className={`h-2.5 w-2.5 rounded-full transition-all
                        ${active ? "bg-primary-purple scale-100" : "bg-transparent scale-0"}`}
          />
        </span>
      </button>
    );
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Business Type"
              current={2}
              total={6}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4 sm:mt-0 mt-4">
          <div className="w-full max-w-lg">
           

            {/* Type Grid / Read-only */}
            <div className="mb-4">
              <label className="block text-[11px] text-primary-blue font-semibold mb-2">
                Type
              </label>

              {isContractor ? (
                <div className="w-full rounded-3xl bg-white border border-gray-200 px-4 py-3 flex items-center justify-between">
                  <span className="text-xs sm:text-sm text-gray-800">Sole Proprietorship</span>
               
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                  <TypeCard value="sole"         label="Sole Proprietorship" />
                  <TypeCard value="partnership"  label="Partnership" />
                  <TypeCard value="nonprofit"    label="Non-profit" />
                  <TypeCard value="corporation"  label="Corporation" />
                  <TypeCard value="llc"          label="LLC" />
                  <TypeCard value="other"        label="Other" />
                </div>
              )}
            </div>

            {/* State */}
            <div className="mt-4">
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                State
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M3 12h18M12 3a14.5 14.5 0 010 18M12 3a14.5 14.5 0 000 18" />
                  </svg>
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setOpenState((s) => !s);
                    setOpenYears(false);
                    setOpenEmp(false);
                  }}
                  className="w-full pl-12 pr-10 py-4 rounded-full bg-white border border-gray-200 text-left
                             text-xs md:text-sm text-gray-800 outline-none"
                >
                  {usState || "Select your State"}
                </button>

                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${openState ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>

                {openState && (
                  <ul
                    className="absolute z-40 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg
                               overflow-auto max-h-44 sm:max-h-60 text-[11px] sm:text-sm"
                  >
                    {US_STATES.map((s) => (
                      <li key={s}>
                        <button
                          type="button"
                          onClick={() => {
                            setUsState(s);
                            setRegistrationData((prev) => ({ ...prev, usState: s }));
                            setOpenState(false);
                          }}
                          className="w-full text-left px-3 py-2 sm:px-4 sm:py-2.5 hover:bg-primary-purple/5"
                          aria-selected={usState === s}
                        >
                          {s}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Years */}
            <div className="mt-6">
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Years in Business
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                    <path d="M7 4v3M17 4v3M4 9h16M5 20h14a2 2 0 0 0 2-2v-9H3v9a2 2 0 0 0 2 2Z" />
                  </svg>
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setOpenYears((s) => !s);
                    setOpenEmp(false);
                    setOpenState(false);
                  }}
                  className="w-full pl-12 pr-10 py-4 rounded-full bg-white border border-gray-200 text-left
                             text-xs md:text-sm text-gray-800 outline-none"
                >
                  {years || "Select Years in Business"}
                </button>

                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${openYears ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>

                {openYears && (
                  <ul
                    className="absolute z-40 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg
                               overflow-auto max-h-44 sm:max-h-60 text-[11px] sm:text-sm"
                  >
                    {YEARS_OPTIONS.map((opt) => (
                      <li key={opt}>
                        <button
                          type="button"
                          onClick={() => {
                            setYears(opt);
                            setOpenYears(false);
                          }}
                          className="w-full text-left px-3 py-2 sm:px-4 sm:py-2.5 hover:bg-primary-purple/5"
                          aria-selected={years === opt}
                        >
                          {opt}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Employees */}
            <div className="mt-4">
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Employee Count
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                    <path d="M16 11a3 3 0 100-6 3 3 0 000 6Z" />
                    <path d="M8 13a3 3 0 100-6 3 3 0 000 6Z" />
                    <path d="M2 20a6 6 0 0112 0M10 20a6 6 0 0112 0" />
                  </svg>
                </span>

                <button
                  type="button"
                  onClick={() => {
                    setOpenEmp((s) => !s);
                    setOpenYears(false);
                    setOpenState(false);
                  }}
                  className="w-full pl-12 pr-10 py-4 rounded-full bg-white border border-gray-200 text-left
                             text-xs md:text-sm text-gray-800 outline-none"
                >
                  {employees || "Select Employee Count"}
                </button>

                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 transition-transform ${openEmp ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>

                {openEmp && (
                  <ul
                    className="absolute z-40 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg
                              overflow-auto max-h-24 sm:max-h-40 text-[11px] sm:text-sm"
                  >
                    {EMPLOYEE_OPTIONS.map((opt) => (
                      <li key={opt}>
                        <button
                          type="button"
                          onClick={() => {
                            setEmployees(opt);
                            setOpenEmp(false);
                          }}
                          className="w-full text-left px-3 py-1.5 sm:px-4 sm:py-2 hover:bg-primary-purple/5"
                          aria-selected={employees === opt}
                        >
                          {opt}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

              </div>
            </div>

            <Button
              text={loading ? "Saving..." : "Next Company Information"}
              onClick={handleContinue}
              disabled={loading}
            />
          </div>
        </div>
      </div>

      <ToastContainer
        position="top-right"
        autoClose={2000}
        hideProgressBar={false}
        closeOnClick
        pauseOnHover
        draggable
      />
    </div>
  );
};

export default BusinessType;
