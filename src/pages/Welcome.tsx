import React, { useContext, useState, useEffect } from "react";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import companyLogo from "./../assets/figmaIcons/company.png";
import { Link, useNavigate } from "react-router-dom";
import { RegistrationContext } from "../context/RegistrationProvider";

type Card = "company" | "contractor";


const Welcome: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  const [selected, setSelected] = useState<Card>(
    (ctx?.registrationData.profileType as Card) || "company"
  );

  
  const onContinue = () => {
    ctx?.setRegistrationData((prev) => ({ ...prev, profileType: selected }));
    navigate("/BusinessRegistration");
  };


  useEffect(() => {
  ctx?.startSignup();
}, []);



  const CardRow: React.FC<{
    id: Card;
    title: string;
    subtitle: string;
  }> = ({ id, title, subtitle }) => {
    const active = selected === id;
    return (
      <button
        type="button"
        onClick={() => setSelected(id)}
        className="w-full flex items-center gap-4 rounded-3xl md:p-5 p-3 border bg-white
                   shadow-[0_6px_24px_rgba(0,0,0,0.06)] text-left transition
                   hover:shadow-[0_8px_28px_rgba(0,0,0,0.10)] hover:border-primary-purple/50"
        aria-pressed={active}
      >
        <div className="flex items-center justify-center rounded-xl bg-primary-purple/10 w-10 h-10 shrink-0">
            {id === "company" ? (
              <img src={companyLogo} alt="" className="w-5 h-5 object-contain" />
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-5 h-5 text-primary-purple"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 
                        1.79-4 4 1.79 4 4 4zm0 2c-3.33 0-6 1.34-6 
                        3v1h12v-1c0-1.66-2.67-3-6-3z" />
              </svg>
            )}
          </div>
        <div className="flex-1">
          <div className="font-semibold text-primary-blue leading-tight sm:text-2xl text-lg">
            {title}
          </div>
          <div className="sm:text-xs text-[10px] text-primary-blue font-medium pt-2">{subtitle}</div>
        </div>

        <span
          className={`relative h-6 w-6 rounded-full border flex items-center justify-center
                      ${active ? "border-primary-purple" : "border-gray-300"}`}
          aria-label={active ? "Selected" : "Not selected"}
        >
          <span
            className={`h-3.5 w-3.5 rounded-full transition-all
                        ${active ? "bg-primary-purple scale-100" : "bg-transparent scale-0"}`}
          />
        </span>
      </button>
    );
  };


  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold sm:text-4xt text-3xl text-center">
              Welcome and Choose <br className="hidden md:block" /> Your Profile Type
            </h1>
            <p className="text-xs text-gray-700 text-center">
              We’ve sent the code to the email on your device
            </p>
          </div>

          <div className="space-y-4">
            <CardRow id="company" title="Company" subtitle="Company user" />
            <CardRow id="contractor" title="Independent Contractor" subtitle="Individual user" />
          </div>

          <div className="mt-6">
            <Button text="Register" onClick={onContinue} />
          </div>

          <p className="mt-8 text-center text-xs text-gray-600">
            Already have an account?{" "}
            <Link
              to="/Login"
              className="text-primary-purple font-semibold underline-offset-2 inline-block hover:scale-[103%] duration-300"
            >
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
