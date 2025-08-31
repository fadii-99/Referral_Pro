import React, { useState } from "react";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import messageIcon from "./../assets/figmaIcons/sms.svg";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const serverUrl = import.meta.env.VITE_SERVER_URL;

type ForgotForm = {
  email: string;
};

const digitsOnly = (v: string) => v.replace(/\D/g, "");

const Forget: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<ForgotForm>({ email: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const resetHandler: React.MouseEventHandler<HTMLButtonElement> = async () => {
    const email = form.email.trim();
    if (!email) {
      toast.error("Please enter your email");
      return;
    }

    setLoading(true);

    const fd = new FormData();
    fd.append("email", email);

    // persist for next screen
    localStorage.setItem("Email", email);

    try {
      const url = new URL(`${serverUrl}/auth/send_otp/`);

      const res = await fetch(url.toString(), {
        method: "POST",
        body: fd,
        cache: "no-store"
      });

      const ct = res.headers.get("content-type") || "";
      let data: any = null;
      if (ct.includes("application/json")) {
        try {
          data = await res.json();
        } catch {
          data = null;
        }
      } else {
        try {
          data = await res.text();
        } catch {
          data = null;
        }
      }

      if (!res.ok) {
        console.groupCollapsed(`❌ send_otp failed ${res.status} ${res.statusText}`);
        console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
        console.groupEnd();

        const msg =
          (data && (data.error || data.detail || data.message)) ||
          (res.status === 404 ? "No account found with this email" : "Failed to send OTP");
        toast.error(msg);
        return;
      }

      console.groupCollapsed("✅ send_otp success");
      console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
      console.groupEnd();

      toast.success(
        typeof data === "string" ? "OTP sent" : data?.message || "OTP sent"
      );

      navigate("/PasswordVerification", { state: { email } });
    } catch (err) {
      console.error("Forgot password error:", err);
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold sm:text-4xt text-3xl">Forgot Password</h1>
            <p className="text-xs text-gray-700 text-center">
              Enter your email to receive a reset code
            </p>
          </div>

          <form className="flex flex-col gap-5">
            <div className="w-full">
              <label
                htmlFor="email"
                className="block text-xs text-primary-blue font-medium mb-2"
              >
                Email Address<span className="text-rose-500">*</span>
              </label>

              <div className="relative">
                <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                  <img src={messageIcon} alt="email" className="h-5 w-5" />
                </span>

                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  placeholder="Enter your email address"
                  value={form.email}
                  onChange={handleChange}
                  className="w-full pl-16 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs outline-none text-gray-800 placeholder-gray-400 focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            <Button
              text={loading ? "Sending..." : "Reset Password"}
              onClick={resetHandler}
              disabled={loading}
            />
          </form>
        </div>
      </div>

      <ToastContainer position="top-right" autoClose={2000} hideProgressBar={false} closeOnClick pauseOnHover draggable />
    </div>
  );
};

export default Forget;
