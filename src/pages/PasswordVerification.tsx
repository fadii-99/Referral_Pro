// src/screens/PasswordVerification.tsx
import React, { useEffect, useRef, useState, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { RegistrationContext } from "../context/RegistrationProvider";

const RESEND_WINDOW = 85; // seconds
const serverUrl = import.meta.env.VITE_SERVER_URL;

const PasswordVerification: React.FC = () => {
  const [code, setCode] = useState<string[]>(Array(6).fill(""));
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number>(RESEND_WINDOW);

  const navigate = useNavigate();
  const location = useLocation();
  const emailFromState = (location.state as any)?.email || "";

  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("Wrap your app with <RegistrationProvider />");
  const { setTempToken } = ctx;

  useEffect(() => {
    inputsRef.current[0]?.focus();
  }, []);

  // resend cooldown timer
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const t = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [secondsLeft]);

  const digitsOnly = (s: string) => s.replace(/\D/g, "");
  const joinCode = () => code.join("");
  const isComplete = code.every((c) => c.length === 1);

  const handleChange = (raw: string, idx: number) => {
    const val = digitsOnly(raw);
    if (val.length === 0) {
      const next = [...code];
      next[idx] = "";
      setCode(next);
      return;
    }

    const chars = val.split("");
    const next = [...code];

    let writeIndex = idx;
    for (let i = 0; i < chars.length && writeIndex < 6; i++, writeIndex++) {
      next[writeIndex] = chars[i];
    }
    setCode(next);

    const firstEmpty = next.findIndex((c) => c === "");
    const targetIndex =
      firstEmpty === -1 ? Math.min(writeIndex - 1, 5) : Math.max(idx + 1, Math.min(firstEmpty, 5));

    inputsRef.current[targetIndex]?.focus();
    inputsRef.current[targetIndex]?.select();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, idx: number) => {
    if (e.key === "Backspace") {
      if (code[idx]) {
        const next = [...code];
        next[idx] = "";
        setCode(next);
      } else if (idx > 0) {
        inputsRef.current[idx - 1]?.focus();
        inputsRef.current[idx - 1]?.select();
      }
      return;
    }
    if (e.key === "ArrowLeft" && idx > 0) {
      inputsRef.current[idx - 1]?.focus();
      inputsRef.current[idx - 1]?.select();
    }
    if (e.key === "ArrowRight" && idx < 5) {
      inputsRef.current[idx + 1]?.focus();
      inputsRef.current[idx + 1]?.select();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>, idx: number) => {
    e.preventDefault();
    const text = digitsOnly(e.clipboardData.getData("text")).slice(0, 6 - idx);
    if (!text) return;

    const next = [...code];
    for (let i = 0; i < text.length && idx + i < 6; i++) {
      next[idx + i] = text[i];
    }
    setCode(next);

    const lastIndex = Math.min(idx + text.length - 1, 5);
    inputsRef.current[lastIndex]?.focus();
    inputsRef.current[lastIndex]?.select();
  };

  const handleVerify = async () => {
    if (verifying) return;
    if (!isComplete) {
      toast.error("Please enter the 6-digit code.");
      return;
    }
    setVerifying(true);

    const otp = joinCode();
    const fd = new FormData();
    fd.append("otp", otp);
    fd.append("email", localStorage.getItem("Email") || "");

    try {
      const url = new URL(`${serverUrl}/auth/verify_otp/`);
      const res = await fetch(url.toString(), { method: "POST", body: fd });

      const ct = res.headers.get("content-type") || "";
      let data: any = null;
      if (ct.includes("application/json")) {
        try {
          data = await res.json();
        } catch {}
      } else {
        try {
          data = await res.text();
        } catch {}
      }

      if (!res.ok) {
        console.groupCollapsed(`❌ verify_otp failed ${res.status} ${res.statusText}`);
        console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
        console.groupEnd();
        const msg = (data && (data.error || data.detail || data.message)) || "Verification failed";
        toast.error(msg);
        return;
      }

      if (data && typeof data !== "string" && data.temp_token) {
        setTempToken(data.temp_token); // context only (not persisted)
      }

      localStorage.removeItem("Email");

      navigate("/CreatePassword");
    } catch (err) {
      console.error("Verify error:", err);
      toast.error("Invalid or expired code. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async () => {
    if (resending || secondsLeft > 0) return;
    const email = emailFromState || localStorage.getItem("Email") || "";
    if (!email) {
      toast.error("Email missing. Go back and enter your email again.");
      return;
    }
    setResending(true);

    try {
      const url = new URL(`${serverUrl}/auth/send_otp/`);
      const fd = new FormData();
      fd.append("email", email);

      const res = await fetch(url.toString(), { method: "POST", body: fd });

      const ct = res.headers.get("content-type") || "";
      let data: any = null;
      if (ct.includes("application/json")) {
        try {
          data = await res.json();
        } catch {}
      } else {
        try {
          data = await res.text();
        } catch {}
      }


      if (!res.ok) {
        console.groupCollapsed(`❌ resend_otp failed ${res.status} ${res.statusText}`);
        console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
        console.groupEnd();
        const msg = (data && (data.error || data.detail || data.message)) || "Resend failed";
        toast.error(msg);
        return;
      }

      toast.success(typeof data === "string" ? "OTP sent" : data?.message || "OTP sent");
      setCode(Array(6).fill(""));
      inputsRef.current[0]?.focus();
      setSecondsLeft(RESEND_WINDOW);
    } catch (err) {
      console.error("Resend error:", err);
      toast.error("Network error. Please try again.");
    } finally {
      setResending(false);
    }
  };

  
  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      {/* Right pane */}
      <div className="md:col-span-3 flex items-center justify-center px-4 sm:px-6 md:px-8 py-8">
        <div className="w-full max-w-lg">
          {/* Heading */}
          <div className="flex flex-col items-center gap-2 sm:gap-3 mb-6 sm:mb-8">
            <h1 className="text-primary-blue font-semibold sm:text-4xt text-3xl text-center leading-tight">
              Enter your passcode
            </h1>
            <p className="text-[11px] sm:text-xs md:text-sm text-gray-700 text-center">
              We’ve sent the code to the email on your device
            </p>
          </div>

          <form
            className="flex flex-col gap-5 sm:gap-6"
            onSubmit={(e) => {
              e.preventDefault();
              void handleVerify();
            }}
          >
            {/* OTP inputs — responsive & wrap-safe */}
            <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 md:gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <input
                  key={i}
                  ref={(el) => {
                    inputsRef.current[i] = el;
                  }}
                  type="tel"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  autoComplete="one-time-code"
                  maxLength={1}
                  value={code[i]}
                  onChange={(e) => handleChange(e.target.value, i)}
                  onKeyDown={(e) => handleKeyDown(e, i)}
                  onPaste={(e) => handlePaste(e, i)}
                  placeholder="-"
                  className="w-10 h-12 sm:w-12 sm:h-12 md:w-14 md:h-14 lg:w-16 lg:h-16
                             text-center text-base sm:text-lg md:text-xl font-medium
                             rounded-2xl bg-white border border-gray-200 placeholder-gray-300
                             outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              ))}
            </div>

            {/* Resend row */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
              <span className="text-xs sm:text-sm font-medium text-primary-purple/80" aria-live="polite">
                {secondsLeft > 0 ? `Resend code in ${secondsLeft} sec` : "You can resend the code now"}
              </span>

              <button
                type="button"
                onClick={handleResend}
                disabled={secondsLeft > 0 || resending}
                className={`text-sm font-semibold underline-offset-2 transition ${
                  secondsLeft > 0 || resending
                    ? "text-gray-400 cursor-not-allowed"
                    : "text-primary-purple hover:text-primary-purple/90"
                }`}
              >
                {resending ? "Resending..." : "Resend"}
              </button>
            </div>

            <Button
              text={verifying ? "Verifying..." : "Submit"}
              onClick={() => void handleVerify()}
              disabled={verifying || !isComplete}
            />
          </form>
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

export default PasswordVerification;
