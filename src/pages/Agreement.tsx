import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

const US_STATES = [
  "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
  "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky",
  "Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi",
  "Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico",
  "New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
  "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
  "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
];

const Agreement: React.FC = () => {
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [state, setState] = useState<string>("");
  const [agree, setAgree] = useState<boolean>(true); 

  const onNext: React.MouseEventHandler<HTMLButtonElement> = () => {

    navigate("/InviteMember"); 
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader title="Agreement" current={6} total={7} onBack={() => navigate(-1)} />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            <div className="mb-4">
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                State
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 text-primary-purple/80"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path d="M3 12h18M12 3a14.5 14.5 0 010 18M12 3a14.5 14.5 0 000 18" />
                  </svg>
                </span>

                <button
                  type="button"
                  onClick={() => setOpen((s) => !s)}
                  className="w-full pl-12 pr-10 py-4 rounded-full bg-white border border-gray-200 text-left
                             text-xs md:text-sm text-gray-800 outline-none"
                >
                  {state || "Select your State"}
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
                  <ul className="absolute z-20 mt-2 max-h-64 overflow-auto w-full bg-white border border-gray-200 rounded-2xl shadow-lg">
                    {US_STATES.map((s) => (
                      <li key={s}>
                        <button
                          type="button"
                          onClick={() => {
                            setState(s);
                            setOpen(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-primary-purple/5"
                          aria-selected={state === s}
                        >
                          {s}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <label className="flex items-start gap-3 text-[12px] text-primary-blue">
                <input
                  type="checkbox"
                  checked={agree}
                  onChange={(e) => setAgree(e.target.checked)}
                  className="mt-[2px] h-4 w-4 rounded-sm border border-gray-300 text-primary-purple
                             focus:ring-1 focus:ring-primary-blue/30 checked:bg-primary-purple checked:border-primary-purple"
                />
                <span className="leading-5 text-primary-purple">
                  I agree to comply with all applicable laws and regulations regarding
                  referral fees for legal services.
                </span>
              </label>

              <div className="flex items-start gap-2 text-[12px] text-gray-600">
                <span className="mt-[2px]">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 text-gray-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 8h.01M11 12h2v4h-2z" />
                  </svg>
                </span>
                <span>No referral fees for legal services in Florida.</span>
              </div>
            </div>
              <Button text="Next Add Invite Team Members" onClick={onNext} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Agreement;
