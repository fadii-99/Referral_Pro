// screens/PasswordCreation.tsx
import React, { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader"; // ✅ ADD
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";
import lockIcon from "./../assets/figmaIcons/lock.png";
import { RegistrationContext } from "../context/RegistrationProvider";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PasswordCreation: React.FC = () => {
  const navigate = useNavigate();

  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("PasswordCreation must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  // hydrate from context so reload pe dikhe
  const [password, setPassword] = useState(registrationData.password || "");
  const [confirmPassword, setConfirmPassword] = useState(registrationData.password || "");
  const [showPwd, setShowPwd] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agree, setAgree] = useState(false);

  // (optional) if context changes elsewhere, keep in sync
  useEffect(() => {
    setPassword(registrationData.password || "");
    setConfirmPassword(registrationData.password || "");
  }, [registrationData.password]);

  const handleConfirm: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (!password.trim() || !confirmPassword.trim()) {
      toast.error("Please fill out all fields.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }
    if (!agree) {
      toast.error("Please accept the agreement to continue.");
      return;
    }

    // Save to context
    setRegistrationData(prev => ({
      ...prev,
      password: password.trim(),
    }));

    toast.success("Password created successfully!");
    navigate("/SubscriptionPlan");
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      {/* ✅ Make right side like SubscriptionPlan: flex-col + sticky header */}
      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        {/* Sticky header bar */}
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Create Password"
              current={4}      // ← adjust if your step order differs
              total={7}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            <div className="flex flex-col items-center gap-2 mb-8">
              <h1 className="text-primary-blue font-semibold text-3xl md:text-4xl text-center">
                Create new password
              </h1>
              <p className="text-xs text-gray-700 text-center">
                Use a new password you haven&apos;t used before.
              </p>
            </div>

            <div className="flex flex-col gap-5">
              {/* Password */}
              <div>
                <label className="block text-xs text-primary-blue font-semibold mb-2">
                  Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-5 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={lockIcon} alt="lock" className="h-5 w-5" />
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPwd(s => !s)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple"
                  >
                    {showPwd ? <AiOutlineEyeInvisible className="h-5 w-5" /> : <AiOutlineEye className="h-5 w-5" />}
                  </button>
                  <input
                    type={showPwd ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-12 py-5 rounded-full bg-white border border-gray-200 text-sm
                               text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-xs text-primary-blue font-semibold mb-2">
                  Confirm Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-5 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={lockIcon} alt="lock" className="h-5 w-5" />
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowConfirm(s => !s)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple"
                  >
                    {showConfirm ? <AiOutlineEyeInvisible className="h-5 w-5" /> : <AiOutlineEye className="h-5 w-5" />}
                  </button>
                  <input
                    type={showConfirm ? "text" : "password"}
                    placeholder="Enter Confirm Password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-12 pr-12 py-5 rounded-full bg-white border border-gray-200 text-sm
                               text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Agreement */}
              <label className="flex items-center gap-2 text-xs text-primary-blue">
                <input
                  type="checkbox"
                  checked={agree}
                  onChange={(e) => setAgree(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary-purple
                             focus:ring-primary-purple checked:bg-primary-purple checked:border-primary-purple"
                />
                <span>I agree to the terms & conditions</span>
              </label>

              <Button text="Confirm" onClick={handleConfirm} />
            </div>
          </div>
        </div>
      </div>

      <ToastContainer position="top-right" autoClose={2000} hideProgressBar={false} closeOnClick pauseOnHover draggable />
    </div>
  );
};

export default PasswordCreation;
