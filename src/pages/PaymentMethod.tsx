// src/screens/PaymentMethod.tsx
import React, { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "../components/MultiStepHeader";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { RegistrationContext } from "../context/RegistrationProvider";

const serverUrl = import.meta.env.VITE_SERVER_URL;

const digitsOnly = (v: string) => v.replace(/\D/g, "");
const formatCard = (raw: string) => {
  const d = digitsOnly(raw).slice(0, 16);
  return d.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
};
const toMMYY = (yyyyMM: string) => {
  if (!/^\d{4}-\d{2}$/.test(yyyyMM)) return "";
  const [y, m] = yyyyMM.split("-");
  return `${m}/${y.slice(-2)}`;
};


const PaymentMethod: React.FC = () => {
  const navigate = useNavigate();

  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("Wrap your app with <RegistrationProvider /> first.");
  const { registrationData, finishSignup } = ctx;

  const [cardName, setCardName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expMonthValue, setExpMonthValue] = useState("");
  const [cvv, setCvv] = useState("");

  const [submitting, setSubmitting] = useState(false);

  // 🔽 states for custom dropdowns
  const [openMonth, setOpenMonth] = useState(false);
  const [openYear, setOpenYear] = useState(false);

  const cardDigitsCount = useMemo(() => digitsOnly(cardNumber).length, [cardNumber]);
  const onChangeCardNumber = (val: string) => setCardNumber(formatCard(val));
  const onChangeCVV = (val: string) => setCvv(digitsOnly(val).slice(0, 3));



 const onSave: React.MouseEventHandler<HTMLButtonElement> = async () => {
  if (submitting) return;

  if (!cardName.trim() || !cardNumber.trim() || !expMonthValue || !cvv.trim()) {
    toast.error("Please fill out card name, number, expiry and CVV.");
    return;
  }
  if (cardDigitsCount !== 16) {
    toast.error("Card number must be 16 digits.");
    return;
  }
  if (cvv.length !== 3) {
    toast.error(
      cvv.length > 3
        ? "CVV is too long (3 digits required)."
        : "CVV is too short (3 digits required)."
    );
    return;
  }

  // 🔄 expiry validation
  const [expYear, expMonth] = expMonthValue.split("-");
  if (!expYear || expYear === "0000") {
    toast.error("Please select expiry year.");
    return;
  }
  if (!expMonth || expMonth === "00") {
    toast.error("Please select expiry month.");
    return;
  }

  setSubmitting(true);

  try {
    const isCompany = registrationData.profileType === "company";
    const expMMYY = toMMYY(expMonthValue);

    const payload = {
      welcome: {
        role: "Business",
        profileType: registrationData.profileType || "",
      },
      basic: {
        firstName: registrationData.firstName,
        lastName: registrationData.lastName,
        industry: registrationData.industry,
        email: registrationData.email,
        ...(isCompany ? { companyName: registrationData.companyName } : {}),
      },
      businessType: {
        type: isCompany ? registrationData.bizType || "sole" : "sole",
        years: registrationData.years,
        employees: registrationData.employees,
        usState: registrationData.usState,
      },
      companyInfo: {
        address1: registrationData.address1,
        address2: registrationData.address2,
        city: registrationData.city,
        postCode: registrationData.postCode,
        phone: registrationData.phone,
        website: registrationData.website,
      },
      subscription: {
        billing: registrationData.subscriptionBilling,
        planId:
          registrationData.subscriptionPlanId === null
            ? null
            : Number(registrationData.subscriptionPlanId),
        seats: Number(registrationData.subscriptionSeats),
        currency: registrationData.subscriptionCurrency || "USD",
        total: Number(registrationData.subscriptionTotal || 0),
        totalDisplay: registrationData.subscriptionTotalDisplay || "",
      },
      payment: {
        paymentType: registrationData.paymentType,
        charge: {
          currency: registrationData.subscriptionCurrency || "USD",
          total: Number(registrationData.subscriptionTotal || 0),
          totalDisplay: registrationData.subscriptionTotalDisplay || "",
        },
        card: {
          name: cardName.trim(),
          number: digitsOnly(cardNumber),
          expiry: { monthValue: expMonthValue, mmYY: expMMYY },
          cvv,
        },
      },
      password: {
        value: registrationData.password || "",
      },
    };

    console.log("🚀 Final Payload Sent to Backend:", payload);

    const fd = new FormData();
    fd.append("payload", JSON.stringify(payload));

       const res = await fetch(`${serverUrl}/auth/sign_up/`, {
          method: "POST",
          body: fd,
        });

        const data = await res.json();

        if (!res.ok) {
          const msg =
            data.error || data.detail || data.message || "Payment submit failed";

          toast.error(msg);
          return;
        }

        toast.success("Signup successful!");
        setTimeout(() => {
          finishSignup({ clear: true });
          setCardName("");
          setCardNumber("");
          setExpMonthValue("");
          setCvv("");
          navigate("/Login", { replace: true });
        }, 2000);



  } catch (e) {
    console.error(e);
    toast.error("Something went wrong. Try again.");
  } finally {
    setSubmitting(false); // ✅ always reset
  }
};



  const isStripe = registrationData.paymentType === "stripe";

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Payment Method"
              current={6}
              total={6}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {/* Card Name */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">
                  Card Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-primary-purple/80"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    >
                      <path d="M12 12a4 4 0 100-8 4 4 0 000 8Z" />
                      <path d="M3 20a9 9 0 0118 0" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    placeholder="Card Name"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Card Number */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">
                  Card Number <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-primary-purple/80"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    >
                      <rect x="3" y="5" width="18" height="14" rx="2" />
                      <path d="M3 10h18" />
                    </svg>
                  </span>
                  <input
                    inputMode="numeric"
                    maxLength={19}
                    placeholder="0000 0000 0000 0000"
                    value={cardNumber}
                    onChange={(e) => onChangeCardNumber(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>

              {/* Expiry */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">
                  Expiry <span className="text-rose-500">*</span>
                </label>
                <div className="relative flex items-center gap-2">
                  {/* Icon */}
                  <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 z-10">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-primary-purple/80"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    >
                      <path d="M7 4v3M17 4v3M4 9h16M5 20h14a2 2 0 0 0 2-2v-9H3v9a2 2 0 0 0 2 2Z" />
                    </svg>
                  </span>

                  {/* Month Dropdown */}
               <div className="relative w-1/2">
                    <button
                      type="button"
                      onClick={() => {
                        setOpenMonth((s) => !s);
                        setOpenYear(false);
                      }}
                      className="w-full pl-12 pr-8 py-4 rounded-full bg-white border border-gray-200 text-left text-xs md:text-sm text-gray-800 outline-none"
                    >
                      {expMonthValue.split("-")[1] || "MM"}
                    </button>
                    {openMonth && (
                      <ul className="absolute z-40 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg overflow-auto max-h-44 text-[11px] sm:text-sm">
                        {Array.from({ length: 12 }, (_, i) => {
                          const val = String(i + 1).padStart(2, "0");
                          return (
                            <li key={val}>
                              <button
                                type="button"
                                onClick={() => {
                                  const [curYear] = expMonthValue.split("-");
                                  setExpMonthValue(`${curYear || ""}-${val}`);
                                  setOpenMonth(false);
                                }}
                                className="w-full text-left px-3 py-2 hover:bg-primary-purple/5"
                              >
                                {val}
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>

                  {/* Year Dropdown */}
                  <div className="relative w-1/2">
                    <button
                      type="button"
                      onClick={() => {
                        setOpenYear((s) => !s);
                        setOpenMonth(false);
                      }}
                      className="w-full pl-4 pr-8 py-4 rounded-full bg-white border border-gray-200 text-left text-xs md:text-sm text-gray-800 outline-none"
                    >
                      {expMonthValue.split("-")[0] || "YYYY"}
                    </button>
                    {openYear && (
                      <ul className="absolute z-40 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg overflow-auto max-h-44 text-[11px] sm:text-sm">
                        {Array.from({ length: 15 }, (_, i) => {
                          const year = new Date().getFullYear() + i;
                          return (
                            <li key={year}>
                              <button
                                type="button"
                                onClick={() => {
                                  const [, curMonth] = expMonthValue.split("-");
                                  setExpMonthValue(`${year}-${curMonth || ""}`);
                                  setOpenYear(false);
                                }}
                                className="w-full text-left px-3 py-2 hover:bg-primary-purple/5"
                              >
                                {year}
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>

                </div>
              </div>

              {/* CVV */}
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">
                  CVV <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-primary-purple/80"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    >
                      <path d="M12 2l7 4v6c0 5-3.5 9-7 10-3.5-1-7-5-7-10V6l7-4z" />
                      <path d="M12 11v4" />
                      <circle cx="12" cy="9" r="1" />
                    </svg>
                  </span>
                  <input
                    inputMode="numeric"
                    placeholder="CVV"
                    value={cvv}
                    onChange={(e) => onChangeCVV(e.target.value)}
                    maxLength={3}
                    className="w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200 text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none"
                  />
                </div>
              </div>
            </div>

            <p className="text-[11px] text-gray-500 text-center">
              {isStripe
                ? "Payments secured by Stripe"
                : "Bank transfer will be processed manually"}
            </p>

            <Button
              text={submitting ? "Processing..." : "Save & Continue"}
              onClick={onSave}
              disabled={submitting}
            />

            <p className="mt-2 text-center text-[11px] text-gray-500">
              Terms of Service | Privacy Policy
            </p>
          </div>
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

export default PaymentMethod;
