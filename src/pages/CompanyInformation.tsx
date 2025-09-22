import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

import { HiOutlineHome, HiOutlineLocationMarker, HiOutlineOfficeBuilding, HiOutlineGlobeAlt } from "react-icons/hi";



import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { RegistrationContext } from "../context/RegistrationProvider";

import {
  getCountries,
  getCountryCallingCode,
  parsePhoneNumberFromString,
  getExampleNumber,
} from "libphonenumber-js";
// 👇 TypeScript ko chup karane ke liye any
import rawMetadata from "libphonenumber-js/metadata.full.json";
const metadata: any = rawMetadata;

// Build full country list A → Z
const countries = getCountries()
  .map((code) => ({
    code,
    dialCode: `+${getCountryCallingCode(code)}`,
    name: new Intl.DisplayNames(["en"], { type: "region" }).of(code) || code,
  }))
  .sort((a, b) => a.name.localeCompare(b.name));

const CompanyInformation: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx)
    throw new Error("CompanyInformation must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  const [address1, setAddress1] = useState(registrationData.address1);
  const [address2, setAddress2] = useState(registrationData.address2);
  const [city, setCity] = useState(registrationData.city);
  const [postCode, setPostCode] = useState(registrationData.postCode);
  const [website, setWebsite] = useState(registrationData.website);

  // Phone + Country
  const [country, setCountry] = useState("PK"); // Default Pakistan
  const [localPhone, setLocalPhone] = useState(""); // User entered part
  const [openDropdown, setOpenDropdown] = useState(false);

  // Sync registration data
  useEffect(() => {
    setAddress1(registrationData.address1);
    setAddress2(registrationData.address2);
    setCity(registrationData.city);
    setPostCode(registrationData.postCode);
    setWebsite(registrationData.website);

    if (registrationData.phone) {
      const parsed = parsePhoneNumberFromString(registrationData.phone);
      if (parsed) {
        setCountry(parsed.country || "PK");
        setLocalPhone(parsed.nationalNumber.toString());
      }
    }
  }, [registrationData]);

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (
      !address1.trim() ||
      !city.trim() ||
      !postCode.trim() ||
      !localPhone.trim() ||
      !website.trim()
    ) {
      toast.error("Please fill out all required fields.");
      return;
    }

    // Postcode must be numeric
    const postCodeRegex = /^[0-9]+$/;
    if (!postCodeRegex.test(postCode.trim())) {
      toast.error("Please enter a valid numeric postal code without spaces.");
      return;
    }

    // City must contain only letters & spaces
    const cityRegex = /^[A-Za-z ]+$/;
    if (!cityRegex.test(city.trim())) {
      toast.error(
        "City name should only contain letters and spaces (no numbers or special characters)."
      );
      return;
    }

    // Website validation (basic domain check)
    const websiteRegex =
      /^www\.[^\s]+\.(com|org|net|edu|gov|mil|info|biz|xyz|online|io|ai|tech|app|dev)(\.[a-z]{2,3})?$/i;
    if (!websiteRegex.test(website.trim())) {
      toast.error(
        "Please enter a valid website address (e.g., www.example.com or www.example.com.pk)."
      );
      return;
    }

    // Build full phone number string
    const dialCode = countries.find((c) => c.code === country)?.dialCode || "";
    const fullPhone = `${dialCode}${localPhone}`;

    // Phone validation
    const parsed = parsePhoneNumberFromString(fullPhone);
    let expectedLength: number | null = null;

    try {
      const exampleNum = getExampleNumber(country as any, metadata);
      if (exampleNum) {
        expectedLength = exampleNum.nationalNumber.toString().length;
      }
    } catch {
      expectedLength = null;
    }

    if (!parsed || !parsed.isValid()) {
      const example = countries.find((c) => c.code === country);
      let msg = `Phone number for ${example?.name || country} must be valid.`;
      if (expectedLength) {
        msg = `Phone number for ${example?.name || country} must be valid and contain ${expectedLength} digits.`;
      }
      toast.error(msg);
      return;
    }

    setRegistrationData((prev) => ({
      ...prev,
      address1: address1.trim(),
      address2: address2.trim(),
      city: city.trim(),
      postCode: postCode.trim(),
      phone: parsed.number, // full formatted number like +923001234567
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
              total={6}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg space-y-4">
              {/* Address Line 1 */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                  Address Line 1 <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-purple">
                    <HiOutlineHome className="h-5 w-5" />
                  </span>
                  <input
                    type="text"
                    placeholder="Enter your address"
                    value={address1}
                    onChange={(e) => setAddress1(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 
                              text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Address Line 2 */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                  Address Line 2
                </label>
                <div className="relative">
                   <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-purple">
                    <HiOutlineHome className="h-5 w-5" />
                  </span>
                  <input
                    type="text"
                    placeholder="Enter your address"
                    value={address2}
                    onChange={(e) => setAddress2(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 
                              text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

            {/* City + Post Code */}
            <div className="grid grid-cols-2 gap-3 md:gap-4">
               <div>
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    City
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-purple">
                      <HiOutlineOfficeBuilding className="h-5 w-5" />
                    </span>
                    <input
                      type="text"
                      placeholder="Enter City"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 
                                text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                    />
                  </div>
                </div>

                {/* Post Code */}
                <div>
                  <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                    Post Code
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-purple">
                      <HiOutlineLocationMarker className="h-5 w-5" />
                    </span>
                    <input
                      type="text"
                      placeholder="Enter Post Code"
                      value={postCode}
                      onChange={(e) => setPostCode(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 
                                text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                    />
                  </div>
            </div>
            </div>

            {/* Phone with Custom Dropdown */}
            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Business Phone Number
              </label>
              <div className="relative flex">
                {/* Custom Dropdown Button */}
                <button
                  type="button"
                  onClick={() => setOpenDropdown((s) => !s)}
                  className="pl-3 pr-8 py-4 rounded-l-full bg-white border border-gray-200 text-left text-xs md:text-sm text-gray-800 flex items-center"
                  style={{ minWidth: "100px", height: "48px" }}
                >
                  {countries.find((c) => c.code === country)?.dialCode || "+--"}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className={`ml-8 h-3 w-3 text-gray-500 transition-transform ${
                      openDropdown ? "rotate-180" : ""
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Phone Input - Digits Only */}
                <input
                  type="tel"
                  placeholder="Enter Phone"
                  value={localPhone}
                  onChange={(e) => {
                    const onlyDigits = e.target.value.replace(/\D/g, ""); // allow only numbers
                    setLocalPhone(onlyDigits);
                  }}
                  className="flex-1 pl-4 pr-4 py-4 rounded-r-full bg-white border border-gray-200 text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  style={{ height: "48px" }}
                />


                {/* Dropdown List */}
                {openDropdown && (
                  <ul className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded-2xl shadow-lg max-h-52 overflow-auto text-xs md:text-sm z-50">
                    {countries.map((c) => (
                      <li key={c.code}>
                        <button
                          type="button"
                          onClick={() => {
                            setCountry(c.code);
                            setOpenDropdown(false);
                          }}
                          className="w-full flex justify-start gap-3 px-3 py-2 hover:bg-primary-purple/5"
                        >
                          <span className="font-semibold w-12">{c.dialCode}</span>
                          <span>{c.name}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Website */}
            <div>
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Website
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-purple">
                  <HiOutlineGlobeAlt className="h-5 w-5" />
                </span>
                <input
                  type="url"
                  placeholder="Enter Website URL"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 
                            text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                />
              </div>
           </div>

            <Button text="Next Create Your Password" onClick={handleContinue} />
          </div>
        </div>
      </div>

      <ToastContainer
        position="top-right"
        autoClose={3000}
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
