import React, { useState, useContext } from "react";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import lockIcon from "./../assets/figmaIcons/lock.png";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { RegistrationContext } from "../context/RegistrationProvider";

type CreateForm = {
  password: string;
  confirmPassword: string;
};

const serverUrl = import.meta.env.VITE_SERVER_URL;

const CreatePassword: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("Wrap your app with <RegistrationProvider />");
  const { tempToken, setTempToken } = ctx;

  const [form, setForm] = useState<CreateForm>({ password: "", confirmPassword: "" });
  const [show, setShow] = useState<{ pwd: boolean; cpwd: boolean }>({ pwd: false, cpwd: false });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  
  const createPasswordHandler: React.MouseEventHandler<HTMLButtonElement> = async () => {
    if (loading) return;

    if (!form.password || !form.confirmPassword) {
      toast.error("Please fill both password fields.");
      return;
    }
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }

  

    setLoading(true);

    const fd = new FormData();
    fd.append("new_password", form.password);
    fd.append("temp_token", tempToken);

    try {
      const res = await fetch(`${serverUrl}/auth/reset_password/`, {
        method: "POST",
        body: fd,
      });

      // parse JSON or text safely
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
        const msg =
          (data && typeof data !== "string" && (data.error || data.detail || data.message)) ||
          (typeof data === "string" ? data : "Could not set password");
        toast.error(msg);
        return;
      }

      toast.success(
        typeof data === "string" ? "Password set successfully" : data?.message || "Password set successfully"
      );

      
      // cleanup in-memory token then move on
      setTempToken("");
      navigate("/PasswordSuccess");
    } catch (err) {
      console.error("Create password error:", err);
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      {/* Left side art */}
      <SideDesign />

      {/* Right side content */}
      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          {/* Heading */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold sm:text-4xl text-3xl">
              Create new password
            </h1>
            <p className="text-[11px] sm:text-xs md:text-sm text-center">
              Use a new password you haven&apos;t used before.
            </p>
          </div>

          {/* Form */}
          <form className="flex flex-col gap-5">
            {/* Password */}
            <div className="w-full">
              <label
                htmlFor="password"
                className="block text-xs text-primary-blue font-medium mb-2"
              >
                Password<span className="text-rose-500">*</span>
              </label>

              <div className="relative">
                <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                  <img src={lockIcon} alt="password" className="h-5 w-5" />
                </span>

                <button
                  type="button"
                  aria-label={show.pwd ? "Hide password" : "Show password"}
                  onClick={() => setShow((s) => ({ ...s, pwd: !s.pwd }))}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-primary-purple hover:opacity-90 transition"
                >
                  {show.pwd ? (
                    <AiOutlineEyeInvisible className="h-5 w-5" />
                  ) : (
                    <AiOutlineEye className="h-5 w-5" />
                  )}
                </button>

                <input
                  id="password"
                  name="password"
                  type={show.pwd ? "text" : "password"}
                  required
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="new-password"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  className="w-full pl-16 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs outline-none text-gray-800 placeholder-gray-400 focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div className="w-full">
              <label
                htmlFor="confirmPassword"
                className="block text-xs text-primary-blue font-medium mb-2"
              >
                Confirm Password<span className="text-rose-500">*</span>
              </label>

              <div className="relative">
                <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                  <img src={lockIcon} alt="confirm password" className="h-5 w-5" />
                </span>

                <button
                  type="button"
                  aria-label={show.cpwd ? "Hide confirm password" : "Show confirm password"}
                  onClick={() => setShow((s) => ({ ...s, cpwd: !s.cpwd }))}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-primary-purple hover:opacity-90 transition"
                >
                  {show.cpwd ? (
                    <AiOutlineEyeInvisible className="h-5 w-5" />
                  ) : (
                    <AiOutlineEye className="h-5 w-5" />
                  )}
                </button>

                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={show.cpwd ? "text" : "password"}
                  required
                  placeholder="Enter Confirm Password"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  className="w-full pl-16 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs outline-none text-gray-800 placeholder-gray-400 focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            <Button
              text={loading ? "Saving..." : "Confirm"}
              onClick={createPasswordHandler}
              disabled={loading}
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

export default CreatePassword;
