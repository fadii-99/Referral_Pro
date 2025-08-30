import React, { useState } from "react";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import { useNavigate } from "react-router-dom";
import messageIcon from "./../assets/figmaIcons/sms.svg";

type ForgotForm = {
  email: string;
};

const Forget: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<ForgotForm>({ email: "" });
  const [loading, setLoading] = useState(false);


  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const resetHandler: React.MouseEventHandler<HTMLButtonElement> = async () => {
    if (!form.email.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("https://jsonplaceholder.typicode.com/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email }),
      });

      const data = await res.json();
      navigate("/PasswordVerification");
    } catch (err) {
      console.error("Forgot password error:", err);
      alert("Dummy API failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  
  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex items-center justify-center px-4">
        <div className="w-full max-w-lg">
          {/* Heading */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <h1 className="text-primary-blue font-semibold text-4xl">
              Forgot Password
            </h1>
            <p className="text-xs text-gray-700 text-center">
              Enter your email to receive a reset code
            </p>
          </div>

          {/* Form */}
          <form className="flex flex-col gap-5">
            {/* Email */}
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
    </div>
  );
};

export default Forget;
