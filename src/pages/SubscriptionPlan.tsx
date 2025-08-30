import React, { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";
import { RegistrationContext } from "../context/RegistrationProvider";

type Billing = "monthly" | "yearly";
type PlanKey = "starter" | "growth";

const PLAN_ORDER: Record<PlanKey, 0 | 1> = { starter: 0, growth: 1 };

const PLAN_META: Record<
  PlanKey,
  { name: string; seatsLabel: string; baseSeats: number; monthlyPrice: number }
> = {
  starter: { name: "Starter", seatsLabel: "5 seats", baseSeats: 5, monthlyPrice: 99 },
  growth: { name: "Growth", seatsLabel: "25 seats", baseSeats: 25, monthlyPrice: 299 },
};

const money = (n: number) => `$${Math.round(n).toLocaleString()}`;
const yearlyWithDiscount = (monthlyTotal: number) => Math.round(monthlyTotal * 12 * 0.9);

/** compute displayed price (same math your cards use) and format */
function computeTotals(plan: PlanKey, mode: Billing) {
  const meta = PLAN_META[plan];
  const cardBaseMonthly = Math.ceil(meta.monthlyPrice / meta.baseSeats) * meta.baseSeats - 1;
  const total = mode === "monthly" ? cardBaseMonthly : yearlyWithDiscount(cardBaseMonthly);
  const display = `${money(total)}${mode === "monthly" ? "/mon" : "/yr"}`;
  return { total, display, currency: "USD" as const };
}

const SubscriptionPlan: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("SubscriptionPlan must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  // Tabs: billing
  const [billing, setBilling] = useState<Billing>(
    (registrationData.subscriptionBilling as Billing) || "monthly"
  );

  // Plan selection (0/1) or null
  const [selectedPlanId, setSelectedPlanId] = useState<0 | 1 | null>(
    registrationData.subscriptionPlanId
  );

  // Payment type selection ("bank" | "stripe" | "")
  const [paymentType, setPaymentType] = useState<"bank" | "stripe" | "">(
    registrationData.paymentType || ""
  );

  const perSeatStarter = useMemo(
    () => Math.ceil(PLAN_META.starter.monthlyPrice / PLAN_META.starter.baseSeats),
    []
  );

  const cardPrice = (plan: PlanKey, mode: Billing) => {
    const meta = PLAN_META[plan];
    const cardBaseMonthly = Math.ceil(meta.monthlyPrice / meta.baseSeats) * meta.baseSeats - 1;
    return mode === "monthly" ? cardBaseMonthly : yearlyWithDiscount(cardBaseMonthly);
    // (Pricing display only; selection stores plan id + seats)
  };

  const handleBillingSwitch = (mode: Billing) => {
    setBilling(mode);

    setRegistrationData((prev) => {
      // if a plan is already selected, recompute totals and stash in context
      let next = { ...prev, subscriptionBilling: mode };
      if (selectedPlanId !== null) {
        const planKey: PlanKey = selectedPlanId === 0 ? "starter" : "growth";
        const totals = computeTotals(planKey, mode);
        next = {
          ...next,
          subscriptionCurrency: totals.currency,
          subscriptionTotal: totals.total,
          subscriptionTotalDisplay: totals.display,
        };
      }
      return next;
    });
    // NOTE: planId/Seats remain as-is; only billing switches as required
  };

  const handleSelectPlan = (plan: PlanKey) => {
    const planId = PLAN_ORDER[plan];
    const seats = PLAN_META[plan].baseSeats;
    const totals = computeTotals(plan, billing);
    setSelectedPlanId(planId);

    setRegistrationData((prev) => ({
      ...prev,
      subscriptionBilling: billing, // current tab value
      subscriptionPlanId: planId,
      subscriptionSeats: seats,
      // NEW: store money in USD
      subscriptionCurrency: totals.currency,
      subscriptionTotal: totals.total,
      subscriptionTotalDisplay: totals.display,
    }));
  };

  const handleSelectPayment = (type: "bank" | "stripe") => {
    setPaymentType(type);
    setRegistrationData((prev) => ({
      ...prev,
      paymentType: type,
    }));
  };

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    // Guard: non-selected by default; proceed only when both picked
    if (selectedPlanId === null || !paymentType) return;
    navigate("/PaymentMethod");
  };

  const PlanCard: React.FC<{ id: PlanKey }> = ({ id }) => {
    const meta = PLAN_META[id];
    const price = cardPrice(id, billing);
    const planId = PLAN_ORDER[id];
    const selected = selectedPlanId === planId;

    return (
      <button
        type="button"
        onClick={() => handleSelectPlan(id)}
        className={[
          "relative w-full rounded-2xl px-5 py-6 text-left border transition-shadow",
          selected
            ? "bg-primary-purple text-white border-primary-purple shadow-lg"
            : "bg-white text-primary-blue border-primary-blue/20 hover:shadow-md",
          "shadow-[0_8px_28px_rgba(0,0,0,0.08)]",
        ].join(" ")}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="text-sm font-semibold opacity-90">{meta.name}</div>
            <div className="mt-1 text-[11px] opacity-70">{meta.seatsLabel}</div>
          </div>
          <div
            className={[
              "w-5 h-5 rounded-full border flex items-center justify-center",
              selected ? "border-white bg-white/20" : "border-primary-blue/30",
            ].join(" ")}
            aria-hidden
          >
            {selected ? <span className="w-2.5 h-2.5 rounded-full bg-white" /> : null}
          </div>
        </div>

        <div className="mt-4">
          <span className="text-3xl font-bold tracking-tight">{money(price)}</span>
          <span className="ml-1 text-sm opacity-80">{billing === "monthly" ? "/mon" : "/yr"}</span>
        </div>

        <div className="mt-2 text-xs opacity-70">
          {billing === "yearly"
            ? "10% off with annual prepayment"
            : `~${money(perSeatStarter)}/seat baseline`}
        </div>
      </button>
    );
  };

  const PaymentCard: React.FC<{
    type: "bank" | "stripe";
    label: string;
    helper?: string;
  }> = ({ type, label, helper }) => {
    const selected = paymentType === type;
    return (
      <button
        type="button"
        onClick={() => handleSelectPayment(type)}
        className={[
          "w-full rounded-xl px-4 py-3 border text-left transition-all",
          selected
            ? "bg-white border-primary-purple ring-2 ring-primary-purple/30"
            : "bg-white border-primary-blue/20 hover:shadow-sm",
        ].join(" ")}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-primary-blue">{label}</div>
            {helper ? (
              <div className="text-[11px] text-primary-blue/70 mt-0.5">{helper}</div>
            ) : null}
          </div>
          <div
            className={[
              "w-5 h-5 rounded-full border flex items-center justify-center",
              selected ? "border-primary-purple" : "border-primary-blue/30",
            ].join(" ")}
          >
            {selected ? <span className="w-2.5 h-2.5 rounded-full bg-primary-purple" /> : null}
          </div>
        </div>
      </button>
    );
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />

      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-5 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader
              title="Subscription Plan"
              current={5}
              total={7}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-lg">
            {/* Billing Tabs */}
            <div className="flex items-center gap-6 text-sm font-semibold text-primary-blue mb-3">
              <button
                type="button"
                onClick={() => handleBillingSwitch("monthly")}
                className={`relative pb-2 ${billing === "monthly" ? "text-primary-purple" : "text-primary-blue/70"}`}
              >
                Monthly
                {billing === "monthly" && (
                  <span className="absolute left-0 -bottom-[2px] h-0.5 w-full bg-primary-purple rounded-full" />
                )}
              </button>

              <button
                type="button"
                onClick={() => handleBillingSwitch("yearly")}
                className={`relative pb-2 ${billing === "yearly" ? "text-primary-purple" : "text-primary-blue/70"}`}
              >
                Yearly
                {billing === "yearly" && (
                  <span className="absolute left-0 -bottom-[2px] h-0.5 w-full bg-primary-purple rounded-full" />
                )}
              </button>
            </div>

            {/* Plan Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <PlanCard id="starter" />
              <PlanCard id="growth" />
            </div>

            {/* Payment Method */}
            <div className="mt-6">
              <div className="text-xs text-primary-blue font-semibold mb-2">
                Payment method
              </div>
              <div className="grid grid-cols-2 gap-3">
                <PaymentCard type="bank" label="Bank Transfer" helper="Manual/Invoice" />
                <PaymentCard type="stripe" label="Stripe" helper="Card checkout" />
              </div>
            </div>

            {/* Quick Summary */}
            <div className="mt-6">
              <div className="text-xs text-primary-blue font-semibold mb-2">Your selection</div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="text-primary-blue/80">Billing</div>
                <div className="text-right text-primary-blue font-semibold">
                  {billing}
                </div>

                <div className="text-primary-blue/80">Plan</div>
                <div className="text-right text-primary-blue font-semibold">
                  {selectedPlanId === 0 ? "Starter" : selectedPlanId === 1 ? "Growth" : "—"}
                </div>

                <div className="text-primary-blue/80">Seats</div>
                <div className="text-right text-primary-blue font-semibold">
                  {selectedPlanId === null
                    ? "—"
                    : (selectedPlanId === 0 ? PLAN_META.starter.baseSeats : PLAN_META.growth.baseSeats)}
                </div>

                <div className="text-primary-blue/80">Payment</div>
                <div className="text-right text-primary-blue font-semibold">
                  {paymentType || "—"}
                </div>

                <div className="text-primary-blue/80">Amount</div>
                <div className="text-right text-primary-blue font-semibold">
                  {registrationData.subscriptionTotalDisplay || "—"}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <Button
                text="Next Add Card Details"
                onClick={handleContinue}
                disabled={selectedPlanId === null || !paymentType}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPlan;
