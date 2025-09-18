import React, { createContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

/** Domain types */
export type BizType = "sole" | "partnership" | "nonprofit" | "corporation" | "llc" | "other" | "";
export type ProfileType = "company" | "contractor" | "";
export type Billing = "monthly" | "yearly";
export type PlanId = 0 | 1 | 3 | null;
export type PaymentType = "bank" | "stripe" | "";

/** Persisted registration data (only during signup) */
export interface RegistrationData {
  profileType: ProfileType;

  // Basic
  firstName: string;
  lastName: string;
  email: string;
  companyName: string;
  industry: string;

  // Business type
  bizType: BizType;
  years: string;
  employees: string;
  usState: string;

  // Company info
  address1: string;
  address2: string;
  city: string;
  postCode: string;
  phone: string;
  website: string;

  // Payment (card)
  cardName: string;
  cardNumber: string;
  expMonthValue: string;
  exp: string;
  cvv: string;
  billingAddress1: string;
  billingAddress2: string;

  // Step 4: Password
  password: string;

  // Subscription
  subscriptionBilling: Billing | "";
  subscriptionPlanId: PlanId;
  subscriptionSeats: number;

  subscriptionCurrency: "USD" | "";
  subscriptionTotal: number;
  subscriptionTotalDisplay: string;

  // Payment method
  paymentType: PaymentType;
}

/** Context value */
export interface RegistrationContextValue {
  registrationData: RegistrationData;
  setRegistrationData: React.Dispatch<React.SetStateAction<RegistrationData>>;

  tempToken: string;
  setTempToken: React.Dispatch<React.SetStateAction<string>>;

  startSignup: () => void;
  finishSignup: (opts?: { clear?: boolean }) => void;
  clearRegistrationData: () => void;

  signupActive: boolean;
}

const DEFAULT_DATA: RegistrationData = {
  profileType: "",
  firstName: "",
  lastName: "",
  email: "",
  companyName: "",
  industry: "",

  bizType: "", 

  years: "",
  employees: "",
  usState: "",

  address1: "",
  address2: "",
  city: "",
  postCode: "",
  phone: "",
  website: "",

  cardName: "",
  cardNumber: "",
  expMonthValue: "",
  exp: "",
  cvv: "",
  billingAddress1: "",
  billingAddress2: "",

  password: "",

  subscriptionBilling: "",
  subscriptionPlanId: null,
  subscriptionSeats: 0,

  subscriptionCurrency: "",
  subscriptionTotal: 0,
  subscriptionTotalDisplay: "",

  paymentType: "stripe",
};

const STORAGE_KEY = "registrationData";
const SCOPE_KEY = "signup:active";

export const RegistrationContext = createContext<RegistrationContextValue | undefined>(undefined);

export function RegistrationProvider({ children }: { children: ReactNode }) {
  const [signupActive, setSignupActive] = useState<boolean>(() => {
    try {
      return sessionStorage.getItem(SCOPE_KEY) === "1";
    } catch {
      return false;
    }
  });

  const [registrationData, setRegistrationData] = useState<RegistrationData>(() => {
    if (!signupActive) return { ...DEFAULT_DATA };
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? (JSON.parse(raw) as Partial<RegistrationData>) : {};
      return { ...DEFAULT_DATA, ...parsed };
    } catch {
      return { ...DEFAULT_DATA };
    }
  });

  useEffect(() => {
    if (!signupActive) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(registrationData));
    } catch {}
  }, [registrationData, signupActive]);

  const [tempToken, setTempToken] = useState<string>("");

  const startSignup = () => {
    try {
      sessionStorage.setItem(SCOPE_KEY, "1");
    } catch {}
    setSignupActive(true);
  };

  const clearRegistrationData = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
    setRegistrationData({ ...DEFAULT_DATA });
  };

  const finishSignup = (opts?: { clear?: boolean }) => {
    try {
      sessionStorage.removeItem(SCOPE_KEY);
    } catch {}
    setSignupActive(false);

    if (opts?.clear) {
      clearRegistrationData();
      setTempToken("");
    }
  };

  return (
    <RegistrationContext.Provider
      value={{
        registrationData,
        setRegistrationData,
        tempToken,
        setTempToken,
        startSignup,
        finishSignup,
        clearRegistrationData,
        signupActive,
      }}
    >
      {children}
    </RegistrationContext.Provider>
  );
}

export default RegistrationProvider;
