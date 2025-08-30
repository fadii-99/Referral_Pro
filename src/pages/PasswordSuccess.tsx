import React from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";


const PasswordSuccess: React.FC = () => {
  const navigate = useNavigate();

  
  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />
      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="flex flex-col items-center gap-5">
            <h1 className="text-primary-blue font-semibold text-4xl md:text-5xl text-center">
              Password Changed!
            </h1>
            <p className="text-xs md:text-sm text-gray-700 text-center">
              We’ve sent a confirmation email to your address.
            </p>

            <div className="w-20 h-20 flex items-center justify-center rounded-full bg-white border border-gray-200 shadow mt-8">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-10 w-10 text-primary-purple"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <p className="text-sm text-gray-700 text-center">
              Your password has been changed successfully.
            </p>

            <Button text='Back to login'  onClick={() => navigate("/login")} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasswordSuccess;
