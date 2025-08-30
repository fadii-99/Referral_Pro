import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { RegistrationContext } from "../context/RegistrationProvider";

const CompanyInformation: React.FC = () => {
  const navigate = useNavigate();

  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("CompanyInformation must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  const [address1, setAddress1] = useState(registrationData.address1);
  const [address2, setAddress2] = useState(registrationData.address2);
  const [city, setCity] = useState(registrationData.city);
  const [postCode, setPostCode] = useState(registrationData.postCode);
  const [phone, setPhone] = useState(registrationData.phone);
  const [website, setWebsite] = useState(registrationData.website);


  useEffect(() => {
    setAddress1(registrationData.address1);
    setAddress2(registrationData.address2);
    setCity(registrationData.city);
    setPostCode(registrationData.postCode);
    setPhone(registrationData.phone);
    setWebsite(registrationData.website);
  }, [registrationData]);


  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (!address1.trim() || !address2.trim() || !city.trim() || !postCode.trim() || !phone.trim() || !website.trim()) {
      toast.error("Please fill out all fields.");
      return;
    }

    setRegistrationData((prev) => ({
      ...prev,
      address1: address1.trim(),
      address2: address2.trim(),
      city: city.trim(),
      postCode: postCode.trim(),
      phone: phone.trim(),
      website: website.trim(),
    }));

    navigate("/PasswordCreation");
  };

  
  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Company Information"
              current={3}
              total={7}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg space-y-4">
            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Address Line 1 <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80"
                       fill="none" stroke="currentColor" strokeWidth="1.6"
                       viewBox="0 0 24 24">
                    <path d="M12 21s7-4.438 7-10a7 7 0 10-14 0c0 5.562 7 10 7 10Z"/>
                    <circle cx="12" cy="11" r="2.5"/>
                  </svg>
                </span>
                <input
                  type="text"
                  placeholder="Enter your address"
                  value={address1}
                  onChange={(e) => setAddress1(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                             text-gray-800 placeholder-gray-400 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Address Line 2 <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80"
                       fill="none" stroke="currentColor" strokeWidth="1.6"
                       viewBox="0 0 24 24">
                    <path d="M12 21s7-4.438 7-10a7 7 0 10-14 0c0 5.562 7 10 7 10Z"/>
                    <circle cx="12" cy="11" r="2.5"/>
                  </svg>
                </span>
                <input
                  type="text"
                  placeholder="Enter your address"
                  value={address2}
                  onChange={(e) => setAddress2(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                             text-gray-800 placeholder-gray-400 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 md:gap-4">
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">City</label>
                <input
                  type="text"
                  placeholder="Enter City"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full pl-4 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                             text-gray-800 placeholder-gray-400 outline-none"
                />
              </div>
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">Post Code</label>
                <input
                  type="text"
                  placeholder="Enter Post Code"
                  value={postCode}
                  onChange={(e) => setPostCode(e.target.value)}
                  className="w-full pl-4 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                             text-gray-800 placeholder-gray-400 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Business Phone Number
              </label>
              <input
                type="tel"
                placeholder="Enter Phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full pl-4 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                           text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Website
              </label>
              <input
                type="url"
                placeholder="Enter Website URL"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                className="w-full pl-4 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm
                           text-gray-800 placeholder-gray-400 outline-none"
              />
            </div>

            <Button text="Next Choose Your Plan" onClick={handleContinue}/>
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

export default CompanyInformation;
