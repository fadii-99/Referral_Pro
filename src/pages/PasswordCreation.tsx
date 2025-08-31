// screens/PasswordCreation.tsx
import React, { useState, useContext, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";
import { AiOutlineEye, AiOutlineEyeInvisible, AiOutlineClose } from "react-icons/ai";
import lockIcon from "./../assets/figmaIcons/lock.png";
import { RegistrationContext } from "../context/RegistrationProvider";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const PasswordCreation: React.FC = () => {
  const navigate = useNavigate();

  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("PasswordCreation must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  const [password, setPassword] = useState(registrationData.password || "");
  const [confirmPassword, setConfirmPassword] = useState(registrationData.password || "");
  const [showPwd, setShowPwd] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agree, setAgree] = useState(false);

  // Modal state
  const [showAgreement, setShowAgreement] = useState(false);
  const modalCloseBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    setPassword(registrationData.password || "");
    setConfirmPassword(registrationData.password || "");
  }, [registrationData.password]);

  // Scroll lock + ESC close + initial focus
  useEffect(() => {
    if (showAgreement) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "Escape") setShowAgreement(false);
      };
      window.addEventListener("keydown", onKey);
      // focus close button after paint
      setTimeout(() => modalCloseBtnRef.current?.focus(), 0);

      return () => {
        window.removeEventListener("keydown", onKey);
        document.body.style.overflow = prev;
      };
    }
  }, [showAgreement]);

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

    setRegistrationData((prev) => ({
      ...prev,
      password: password.trim(),
    }));

    navigate("/SubscriptionPlan");
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      {/* Right side */}
      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        {/* Sticky header */}
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader title="Create Password" current={4} total={6} onBack={() => navigate(-1)} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            <div className="flex flex-col items-center gap-2 mb-8">
              <h1 className="text-primary-blue font-semibold text-3xl md:text-4xl text-center">
                Create your password
              </h1>
            </div>

            <div className="flex flex-col gap-5">
              {/* Password */}
              <div>
                <label className="block text-xs text-primary-blue font-semibold mb-2">
                  Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={lockIcon} alt="lock" className="h-5 w-5" />
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPwd((s) => !s)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple"
                    aria-label={showPwd ? "Hide password" : "Show password"}
                  >
                    {showPwd ? <AiOutlineEyeInvisible className="h-5 w-5" /> : <AiOutlineEye className="h-5 w-5" />}
                  </button>
                  <input
                    type={showPwd ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-16 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs
                               text-gray-800 placeholder-gray-400 outline-none focus:ring-2
                               focus:ring-primary-blue/20 focus:border-primary-blue/50"
                    autoComplete="new-password"
                  />
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-xs text-primary-blue font-semibold mb-2">
                  Confirm Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                    <img src={lockIcon} alt="lock" className="h-5 w-5" />
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowConfirm((s) => !s)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple"
                    aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
                  >
                    {showConfirm ? <AiOutlineEyeInvisible className="h-5 w-5" /> : <AiOutlineEye className="h-5 w-5" />}
                  </button>
                  <input
                    type={showConfirm ? "text" : "password"}
                    placeholder="Enter Confirm Password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-16 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs
                               text-gray-800 placeholder-gray-400 outline-none focus:ring-2
                               focus:ring-primary-blue/20 focus:border-primary-blue/50"
                    autoComplete="new-password"
                  />
                </div>
              </div>

              {/* Agreement with modal trigger */}
              <label className="flex items-start gap-2 text-xs text-primary-blue">
                <input
                  type="checkbox"
                  checked={agree}
                  onChange={(e) => setAgree(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary-purple
                             focus:ring-primary-purple checked:bg-primary-purple checked:border-primary-purple"
                />
                <span className="text-gray-600">
                  I agree to the{" "}
                  <button
                    type="button"
                    onClick={() => setShowAgreement(true)}
                    className="text-primary-purple underline underline-offset-2 hover:opacity-90"
                  >
                    Agreement
                  </button>{" "}
                  and to comply with all applicable laws and regulations on referral fees for legal services.
                </span>
              </label>

              <Button text="Confirm" onClick={handleConfirm} />
            </div>
          </div>
        </div>
      </div>

      {/* Agreement Modal */}
      {showAgreement && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="agreement-title"
          onMouseDown={(e) => {
            // close on overlay click
            if (e.target === e.currentTarget) setShowAgreement(false);
          }}
        >
          {/* overlay */}
          <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" />

          {/* dialog */}
          <div className="relative z-10 mx-4 w-full max-w-lg sm:max-w-xl">
            <div className="rounded-2xl bg-white shadow-xl border border-gray-100">
              <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b">
                <h2 id="agreement-title" className="text-base sm:text-lg font-semibold text-primary-blue">
                  Agreement
                </h2>
                <button
                  ref={modalCloseBtnRef}
                  type="button"
                  onClick={() => setShowAgreement(false)}
                  className="p-2 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-purple"
                  aria-label="Close agreement modal"
                >
                  <AiOutlineClose className="h-5 w-5" />
                </button>
              </div>

              <div className="px-4 sm:px-6 py-4 sm:py-5 max-h-[70vh] overflow-y-auto text-sm leading-6 text-gray-700">
                <p className="mb-3">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor,
                  dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam. Maecenas
                  ligula massa, varius a, semper congue, euismod non, mi.
                </p>
                <p className="mb-3">
                  Proin porttitor, orci nec nonummy molestie, enim est eleifend mi, non fermentum diam nisl sit amet
                  erat. Duis semper. Duis arcu massa, scelerisque vitae, consequat in, pretium a, enim. Pellentesque
                  congue.
                </p>
                <p className="mb-3">
                  Praesent id justo in neque elementum ultrices. Sed vel lectus. Donec odio tempus molestie, porttitor ut,
                  iaculis quis, sem. Phasellus rhoncus. Aenean id metus id velit ullamcorper pulvinar.
                </p>
                <p>
                  Etiam vel tortor sodales tellus ultricies commodo. Suspendisse potenti. Sed egestas, ante et vulputate
                  volutpat, eros pede semper est, vitae luctus metus libero eu augue.
                </p>
              </div>

              <div className="flex justify-end gap-2 px-4 sm:px-6 py-3 sm:py-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowAgreement(false)}
                  className="rounded-full px-4 py-2 text-sm font-medium text-primary-blue hover:bg-gray-100"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => setShowAgreement(false)}
                  className="rounded-full px-4 py-2 text-sm font-semibold text-white bg-primary-purple hover:opacity-90"
                >
                  I Understand
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ToastContainer position="top-right" autoClose={2000} hideProgressBar={false} closeOnClick pauseOnHover draggable />
    </div>
  );
};

export default PasswordCreation;
