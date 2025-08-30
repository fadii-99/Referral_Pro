import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";

const RESEND_WINDOW = 85; // seconds

const PasswordVerification: React.FC = () => {
  const [code, setCode] = useState<string[]>(Array(6).fill(""));
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number>(RESEND_WINDOW);
  const navigate = useNavigate();


  useEffect(() => {
    inputsRef.current[0]?.focus();
  }, []);


  useEffect(() => {
    if (secondsLeft <= 0) return;
    const t = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [secondsLeft]);


  const joinCode = () => code.join("");
  const isComplete = code.every((c) => c.length === 1);
  const sanitize = (s: string) => s.replace(/[^0-9a-z]/gi, "").toUpperCase();


  const handleChange = (raw: string, idx: number) => {
    const val = sanitize(raw);
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
        // clear current
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
    const text = sanitize(e.clipboardData.getData("text")).slice(0, 6 - idx);
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
      alert("Please enter the 6-digit code.");
      return;
    }
    setVerifying(true);
    try {
      const res = await fetch(``, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: joinCode() }),
      });
      if (!res.ok) throw new Error("Verification failed");

      navigate("/CreatePassword");
    } catch (err) {
      console.error("Verify error:", err);
      alert("Invalid or expired code. Please try again.");
    } finally {
      setVerifying(false);
    }
  };


  // .................................................................................................................................


  const handleResend = async () => {
    if (resending || secondsLeft > 0) return;
    setResending(true);
    try {
      const res = await fetch(``, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "resend_otp" }),
      });
      if (!res.ok) throw new Error("Resend failed");

      setCode(Array(6).fill(""));
      inputsRef.current[0]?.focus();

      setSecondsLeft(RESEND_WINDOW);
    } catch (err) {
      console.error("Resend error:", err);
      alert("Could not resend the code. Please try again.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />
      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          {/* Heading */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold text-4xl md:text-5xl text-center">
              Enter your passcode
            </h1>
            <p className="text-xs md:text-sm text-gray-700 text-center">
              We’ve sent the code to the email on your device
            </p>
          </div>

          <form
            className="flex flex-col gap-6"
            onSubmit={(e) => {
              e.preventDefault();
              void handleVerify();
            }}
          >
            {/* OTP boxes */}
            <div className="flex items-center justify-center gap-3 md:gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <input
                  key={i}
                  ref={(el) => {
                    inputsRef.current[i] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  autoComplete="one-time-code"
                  maxLength={6} 
                  value={code[i]}
                  onChange={(e) => handleChange(e.target.value, i)}
                  onKeyDown={(e) => handleKeyDown(e, i)}
                  onPaste={(e) => handlePaste(e, i)}
                  placeholder="-"
                  className="w-14 h-14 md:w-16 md:h-16 text-center text-lg md:text-xl font-medium
                             rounded-2xl bg-white border border-gray-200 placeholder-gray-300
                             outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              ))}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-primary-purple/80" aria-live="polite">
                {secondsLeft > 0
                  ? `Resend code in ${secondsLeft} sec`
                  : "You can resend the code now"}
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
    </div>
  );
};

export default PasswordVerification;
