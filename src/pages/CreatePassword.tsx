import React, { useState } from "react";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import lockIcon from "./../assets/figmaIcons/lock.png";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";

type CreateForm = {
  password: string;
  confirmPassword: string;
};

const API_URL = "https://jsonplaceholder.typicode.com/posts"; // dummy for now

const CreatePassword: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<CreateForm>({ password: "", confirmPassword: "" });
  const [show, setShow] = useState<{ pwd: boolean; cpwd: boolean }>({ pwd: false, cpwd: false });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const createPasswordHandler: React.MouseEventHandler<HTMLButtonElement> = async () => {
    if (!form.password || !form.confirmPassword) {
      alert("Please fill both password fields.");
      return;
    }
    if (form.password.length < 8) {
      alert("Password must be at least 8 characters.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: form.password }),
      });

      if (!res.ok) throw new Error("Failed to set password");
      const data = await res.json();
     
      navigate("/PasswordSuccess");
    } catch (err) {
      console.error("Create password error:", err);
      alert("Could not set password. Try again.");
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
            <h1 className="text-primary-blue font-semibold text-4xl">
              Create new password
            </h1>
            <p className="text-xs text-gray-700 text-center">
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
                {/* left icon (asset) */}
                <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                  <img src={lockIcon} alt="password" className="h-5 w-5" />
                </span>

                {/* toggle visibility */}
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
                {/* left icon (asset) */}
                <span className="absolute left-8 top-1/2 -translate-y-1/2 pointer-events-none">
                  <img src={lockIcon} alt="confirm password" className="h-5 w-5" />
                </span>

                {/* toggle visibility */}
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
    </div>
  );
};

export default CreatePassword;
