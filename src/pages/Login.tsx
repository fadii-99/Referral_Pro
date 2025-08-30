import React, { useState } from "react";
import { Link } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import lockIcon from "./../assets/figmaIcons/lock.png";
import messageIcon from "./../assets/figmaIcons/sms.svg";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";

const serverUrl = import.meta.env.VITE_SERVER_URL;


type LoginForm = {
  email: string;
  password: string;
};


const Login: React.FC = () => {
  const [form, setForm] = useState<LoginForm>({
    email: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const onLoginClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setLoading(true);

     const fd = new FormData();
  fd.append("email", form.email.trim());
  fd.append("password", form.password);


    try {
      const response = await fetch(`${serverUrl}/auth/login/`, {
         method: "POST",
         body: fd, 
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

      const data = await response.json();
      console.log("✅ Login Success:", data);

    } catch (error) {
      console.error("❌ Login Failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      {/* Right side */}
      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold text-4xl">Login</h1>
            <p className="text-xs text-gray-700 text-center">
              Enter your email and password to log in
            </p>
          </div>

          {/* Form */}
          <form className="flex flex-col gap-5">
            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-xs text-primary-blue font-medium mb-2"
              >
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
                  className="w-full pl-14 pr-4 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-xs text-primary-blue font-medium mb-2"
              >
                Password<span className="text-rose-500">*</span>
              </label>

              <div className="relative">
                {/* Left icon */}
                <span className="absolute left-6 top-1/2 -translate-y-1/2">
                  <img src={lockIcon} alt="password" className="h-5 w-5" />
                </span>

                {/* Toggle eye */}
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-purple hover:text-primary-purple/90 transition"
                >
                  {showPassword ? (
                    <AiOutlineEyeInvisible className="h-5 w-5" />
                  ) : (
                    <AiOutlineEye className="h-5 w-5" />
                  )}
                </button>

                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={handleChange}
                  className="w-full pl-14 pr-12 py-5 rounded-full bg-white border border-gray-200 text-xs text-gray-800 placeholder-gray-400 outline-none focus:ring-2 focus:ring-primary-blue/20 focus:border-primary-blue/50"
                />
              </div>
            </div>

            <div className="flex justify-end mt-1">
              <Link
                to="/ForgetPassword"
                className="text-xs font-semibold text-primary-purple/80 hover:text-primary-purple transition hover:scale-[101%]"
              >
                Forgot your password?
              </Link>
            </div>

            <Button
              text={loading ? "Logging in..." : "Login"}
              disabled={loading}
              onClick={onLoginClick}
            />
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
