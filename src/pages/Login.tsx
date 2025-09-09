// src/screens/Login.tsx
import React, { useContext, useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import lockIcon from "../assets/figmaIcons/lock.png";
import messageIcon from "../assets/figmaIcons/sms.svg";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";
import { RegistrationContext } from "../context/RegistrationProvider";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const serverUrl = import.meta.env.VITE_SERVER_URL;

type LoginForm = { email: string; password: string };

const Login: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);

  useEffect(() => {
    ctx?.clearRegistrationData();
    ctx?.setTempToken?.("");
    ctx?.finishSignup({ clear: true });
  }, []);

  const [form, setForm] = useState<LoginForm>({
    email: localStorage.getItem("rememberEmail") || "",
    password: "",
  });
  const [rememberMe, setRememberMe] = useState<boolean>(!!localStorage.getItem("rememberEmail"));
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onLoginClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (loading) return;
    setLoading(true);

    const fd = new FormData();
    fd.append("email", form.email.trim());
    fd.append("password", form.password);

    try {
      const res = await fetch(`${serverUrl}/auth/login/`, {
        method: "POST",
        body: fd,
        // credentials: "include", 
      });

      // --- Just log the response so you can find the token yourself ---
      console.log("[login] status:", res.status, res.statusText);
      const headersDump: Record<string, string> = {};
      res.headers.forEach((v, k) => (headersDump[k] = v));
      // console.log("[login] headers:", headersDump);

      const raw = await res.text();
      
      let json: any = null;
      try {
        json = raw ? JSON.parse(raw) : null;
      } catch {}
      // console.log("[login] json (if parsable):", json);
      // --- end logging ---

      if (!res.ok) {
        const msg =
          (json && typeof json !== "string" && (json.error || json.detail || json.message)) ||
          (typeof json === "string" ? json : raw || "Invalid credentials");
        toast.error(msg);
        return;
      }


       if (json?.tokens?.access) {
  localStorage.setItem("accessToken", json.tokens.access);
}



      // remember me
      if (rememberMe && form.email.trim()) {
        localStorage.setItem("rememberEmail", form.email.trim());
      } else {
        localStorage.removeItem("rememberEmail");
      }

      navigate("/Dashboard");
    } catch (err) {
      console.error("[login] network error:", err);
      toast.error("Network error. Try again.");
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
            <h1 className="text-primary-blue font-semibold sm:text-4xt text-3xl">Login</h1>
            <p className="text-xs text-gray-700 text-center">Enter your email and password to log in</p>
          </div>

          <form className="flex flex-col gap-5" autoComplete="off">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-xs text-primary-blue font-medium mb-2">
                Email Address<span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-6 top-1/2 -translate-y-1/2">
                  <img src={messageIcon} alt="email" className="h-5 w-5" />
                </span>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  placeholder="Enter your email"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                  className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-xs text-primary-blue font-medium mb-2">
                Password<span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-6 top-1/2 -translate-y-1/2">
                  <img src={lockIcon} alt="password" className="h-5 w-5" />
                </span>
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple hover:text-primary-purple/90 transition"
                >
                  {showPassword ? <AiOutlineEyeInvisible className="h-5 w-5" /> : <AiOutlineEye className="h-5 w-5" />}
                </button>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  className="w-full pl-14 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            {/* Remember me + Forgot password */}
            <div className="flex items-center justify-between mt-1">
              <label className="flex items-center gap-2 text-xs text-primary-blue">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary-purple focus:ring-primary-purple checked:bg-primary-purple checked:border-primary-purple"
                />
                <span>Remember me</span>
              </label>

              <Link
                to="/ForgetPassword"
                className="text-xs font-semibold text-primary-purple/80 hover:text-primary-purple transition hover:scale-[101%]"
              >
                Forgot your password?
              </Link>
            </div>

            <Button text={loading ? "Logging in..." : "Login"} disabled={loading} onClick={onLoginClick} />
          </form>

          {/* CTA: Don't have an account? */}
          <p className="mt-6 text-center text-xs text-gray-600">
            Don’t have an account?{" "}
            <Link
              to="/"
              className="text-primary-purple font-semibold underline-offset-2 inline-block hover:scale-[103%] duration-300"
            >
              Sign up
            </Link>
          </p>
        </div>
      </div>

      <ToastContainer position="top-right" autoClose={2000} hideProgressBar={false} closeOnClick pauseOnHover draggable />
    </div>
  );
};

export default Login;
