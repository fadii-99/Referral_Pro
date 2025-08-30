import React, { useContext, useEffect, useMemo, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

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
  const monthRef = useRef<HTMLInputElement>(null);
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("Wrap your app with <RegistrationProvider /> first.");
  const { registrationData, setRegistrationData } = ctx;

  const [cardName, setCardName] = useState(registrationData.cardName ?? "");
  const [cardNumber, setCardNumber] = useState(registrationData.cardNumber ?? "");
  const [expMonthValue, setExpMonthValue] = useState(registrationData.expMonthValue ?? "");
  const [cvv, setCvv] = useState(registrationData.cvv ?? "");

  useEffect(() => {
    setCardName(registrationData.cardName ?? "");
    setCardNumber(registrationData.cardNumber ?? "");
    setExpMonthValue(registrationData.expMonthValue ?? "");
    setCvv(registrationData.cvv ?? "");
  }, [registrationData]);

  const cardDigitsCount = useMemo(() => digitsOnly(cardNumber).length, [cardNumber]);
  const onChangeCardNumber = (val: string) => setCardNumber(formatCard(val));
  const onChangeCVV = (val: string) => setCvv(digitsOnly(val).slice(0, 3));

  const onSave: React.MouseEventHandler<HTMLButtonElement> = async () => {
    const isStripe = registrationData.paymentType === "stripe";
    const isBank = registrationData.paymentType === "bank";

    if (!isStripe && !isBank) {
      toast.error("Please select a payment method (bank or stripe) on the previous step.");
      return;
    }

    // Required for both bank & stripe
    if (!cardName.trim() || !cardNumber.trim() || !expMonthValue || !cvv.trim()) {
      toast.error("Please fill out card name, number, expiry and CVV.");
      return;
    }
    if (cardDigitsCount !== 16) {
      toast.error("Card number must be 16 digits.");
      return;
    }
    if (cvv.length !== 3) {
      toast.error(cvv.length > 3 ? "CVV is too long (3 digits required)." : "CVV is too short (3 digits required).");
      return;
    }
    if (!/^\d{4}-\d{2}$/.test(expMonthValue)) {
      toast.error("Expiry must be a valid month (YYYY-MM).");
      return;
    }

    const expForContext = toMMYY(expMonthValue);

    // Persist into context
    setRegistrationData((prev) => ({
      ...prev,
      cardName: cardName.trim(),
      cardNumber: cardNumber.trim(),
      expMonthValue,
      exp: expForContext,
      cvv,
      // contractor/individual => force sole; company => keep as-is
      bizType: prev.profileType === "company" ? prev.bizType : "sole",
      companyName: prev.profileType === "company" ? prev.companyName : "",
      industry: prev.profileType === "company" ? prev.industry : "",
      employees: prev.profileType === "company" ? prev.employees : "",
    }));


    try {
      const isCompany = registrationData.profileType === "company";
      const expMMYY = toMMYY(expMonthValue);

      const payload = {
        // Step: Welcome
        welcome: {
          role: "Business",
          profileType: registrationData.profileType || "",
        },
        // Step: Basic
        basic: {
          firstName: registrationData.firstName,
          lastName: registrationData.lastName,
          industry: registrationData.industry,
          email: registrationData.email,
          ...(isCompany ? { companyName: registrationData.companyName } : {}),
        },
        // Step: Business type
        businessType: {
          type: isCompany ? (registrationData.bizType || "sole") : "sole",
          years: registrationData.years,
          employees: registrationData.employees,
          usState: registrationData.usState,
        },
        // Step: Company info (postal/contact)
        companyInfo: {
          address1: registrationData.address1,
          address2: registrationData.address2,
          city: registrationData.city,
          postCode: registrationData.postCode,
          phone: registrationData.phone,
          website: registrationData.website,
        },
        // Step: Subscription (now includes USD price)
        subscription: {
          billing: registrationData.subscriptionBilling, // "monthly" | "yearly" | ""
          planId:
            registrationData.subscriptionPlanId === null
              ? null
              : Number(registrationData.subscriptionPlanId), // 0 | 1
          seats: Number(registrationData.subscriptionSeats),
          currency: registrationData.subscriptionCurrency || "USD",
          total: Number(registrationData.subscriptionTotal || 0), // numeric total
          totalDisplay: registrationData.subscriptionTotalDisplay || "", // e.g. "$99/mon"
        },
        // Step: Payment (also echo charge in USD for backend convenience)
        payment: {
          paymentType: registrationData.paymentType, // "bank" | "stripe"
          charge: {
            currency: registrationData.subscriptionCurrency || "USD",
            total: Number(registrationData.subscriptionTotal || 0),
            totalDisplay: registrationData.subscriptionTotalDisplay || "",
          },
          card: {
            name: cardName.trim(),
            number: digitsOnly(cardNumber),
            expiry: {
              monthValue: expMonthValue, // "YYYY-MM"
              mmYY: expMMYY, // "MM/YY"
            },
            cvv,
          },
        },
        // Step: Password
        password: {
          value: registrationData.password || "",
        },
      };

      const fd = new FormData();
      fd.append("payload", JSON.stringify(payload));

      const res = await fetch(`${serverUrl}/auth/sign_up/`, {
        method: "POST",
        body: fd, // no headers
      });

      
      const ct = res.headers.get("content-type") || "";
      const data = ct.includes("application/json") ? await res.json() : await res.text();
      console.log(data.error);

      if (!res.ok) {
        console.groupCollapsed(`Signup error ${res.status}`);
        console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
        console.groupEnd();
        throw new Error(`Payment submit failed (${res.status})`);
      }

      navigate("/Login");
      console.groupCollapsed("Signup success");
      console.log(typeof data === "string" ? data : JSON.stringify(data, null, 2));
      console.groupEnd();
    } catch (e) {
      toast.error("Something went wrong. Try again.");
    }
  };

  const isStripe = registrationData.paymentType === "stripe";

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader title="Payment Method" current={5} total={7} onBack={() => navigate(-1)} />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            {/* Card inputs (always visible now) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">Card Name</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
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

              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">Card Number</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
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

              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">Expiry</label>
                <div
                  className="relative"
                  onClick={() => {
                    const el = monthRef.current;
                    if (!el) return;
                    if ((el as any).showPicker) {
                      (el as any).showPicker();
                    } else {
                      el.focus();
                    }
                  }}
                  role="button"
                  aria-label="Open expiry month picker"
                >
                  <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                      <path d="M7 4v3M17 4v3M4 9h16M5 20h14a2 2 0 0 0 2-2v-9H3v9a2 2 0 0 0 2 2Z" />
                    </svg>
                  </span>

                  <input
                    ref={monthRef}
                    type="month"
                    value={expMonthValue}
                    onChange={(e) => setExpMonthValue(e.target.value)}
                    className={[
                      "w-full pl-12 pr-4 py-4 rounded-full bg-white border border-gray-200",
                      "text-xs md:text-sm text-gray-800 placeholder-gray-400 outline-none",
                      "[&::-webkit-calendar-picker-indicator]:opacity-0",
                      "[&::-webkit-calendar-picker-indicator]:pointer-events-none",
                      "appearance-none",
                      "pointer-events-none",
                    ].join(" ")}
                    aria-haspopup="dialog"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] text-primary-blue font-semibold mb-2">CVV</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary-purple/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
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

            {/* Stripe / Bank hint */}
            <p className="text-[11px] text-gray-500 text-center">
              {isStripe ? "Payments secured by Stripe" : "Bank transfer will be processed manually"}
            </p>

            <Button text="Save & Continue" onClick={onSave} />

            <p className="mt-2 text-center text-[11px] text-gray-500">Terms of Service | Privacy Policy</p>
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
