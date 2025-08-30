import React, { createContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

export type BizType = "sole" | "partnership" | "nonprofit" | "corporation" | "llc" | "other";
export type ProfileType = "company" | "contractor" | "";
export type Billing = "monthly" | "yearly";
export type PlanId = 0 | 1 | null;       // 0: starter, 1: growth
export type PaymentType = "bank" | "stripe" | "";

export interface RegistrationData {
  // Welcome
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

  // Subscription selections
  subscriptionBilling: Billing | "";  // "monthly" | "yearly" | ""
  subscriptionPlanId: PlanId;         // 0 | 1 | null
  subscriptionSeats: number;          // base seats for selected plan

  // NEW: pricing in USD for payload and UI summary
  subscriptionCurrency: "USD" | "";   // keep simple — your prices are in USD
  subscriptionTotal: number;          // numeric amount (monthly or yearly)
  subscriptionTotalDisplay: string;   // pretty string e.g. "$99/mon"

  // payment method
  paymentType: PaymentType;           // "bank" | "stripe" | ""
}

export interface RegistrationContextValue {
  registrationData: RegistrationData;
  setRegistrationData: React.Dispatch<React.SetStateAction<RegistrationData>>;
}

const DEFAULT_DATA: RegistrationData = {
  profileType: "",
  firstName: "",
  lastName: "",
  email: "",
  companyName: "",
  industry: "",

  bizType: "sole",
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

  // NEW defaults for price
  subscriptionCurrency: "",
  subscriptionTotal: 0,
  subscriptionTotalDisplay: "",

  paymentType: "",
};

export const RegistrationContext =
  createContext<RegistrationContextValue | undefined>(undefined);

export function RegistrationProvider({ children }: { children: ReactNode }) {
  const [registrationData, setRegistrationData] = useState<RegistrationData>(() => {
    try {
      const raw = localStorage.getItem("registrationData");
      const parsed = raw ? (JSON.parse(raw) as Partial<RegistrationData>) : {};
      return { ...DEFAULT_DATA, ...parsed };
    } catch {
      return DEFAULT_DATA;
    }
  });

  useEffect(() => {
    localStorage.setItem("registrationData", JSON.stringify(registrationData));
  }, [registrationData]);

  return (
    <RegistrationContext.Provider value={{ registrationData, setRegistrationData }}>
      {children}
    </RegistrationContext.Provider>
  );
}

export default RegistrationProvider;
