import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";
import { RegistrationContext } from "../context/RegistrationProvider";

type Billing = "monthly" | "yearly" | "";
type PlanKey = "starter" | "growth" | "custom";

const PLAN_ORDER: Record<Exclude<PlanKey, "custom">, 0 | 1> = { starter: 0, growth: 1 };

const PLAN_META = {
  starter: { name: "Starter", seatsLabel: "5 seats", baseSeats: 5, monthlyPrice: 99 },
  growth: { name: "Growth", seatsLabel: "25 seats", baseSeats: 25, monthlyPrice: 299 },
};

const money = (n: number) => `$${Math.round(n).toLocaleString()}`;
const yearlyWithDiscount = (monthlyTotal: number) => Math.round(monthlyTotal * 12 * 0.9);

function computeTotals(plan: PlanKey, mode: Billing, customSeats?: number) {
  if (plan === "custom") {
    const perSeat = 20;
    const monthlyTotal = (customSeats || 5) * perSeat;
    const total =
      mode === "monthly" ? monthlyTotal : mode === "yearly" ? monthlyTotal * 12 : 0;
    return {
      total,
      display: total ? `${money(total)}${mode === "monthly" ? "/mon" : "/yr"}` : "—",
      currency: "USD" as const,
    };
  }

  const meta = PLAN_META[plan];
  const cardBaseMonthly =
    Math.ceil(meta.monthlyPrice / meta.baseSeats) * meta.baseSeats - 1;
  const total =
    mode === "monthly"
      ? cardBaseMonthly
      : mode === "yearly"
      ? yearlyWithDiscount(cardBaseMonthly)
      : 0;
  return {
    total,
    display: total ? `${money(total)}${mode === "monthly" ? "/mon" : "/yr"}` : "—",
    currency: "USD" as const,
  };
}

const SubscriptionPlan: React.FC = () => {
  const navigate = useNavigate();
  const ctx = useContext(RegistrationContext);
  if (!ctx) throw new Error("SubscriptionPlan must be used within RegistrationProvider");
  const { registrationData, setRegistrationData } = ctx;

  const [billing, setBilling] = useState<Billing>(
    (registrationData.subscriptionBilling as Billing) || "monthly"
  );

  const [selectedPlanId, setSelectedPlanId] = useState<0 | 1 | 3 | null>(
    registrationData.subscriptionPlanId
  );

  const [paymentType] = useState<"stripe">("stripe"); // Stripe only

  // 🔽 Custom plan state
  const [customSeats, setCustomSeats] = useState<number>(
    registrationData.subscriptionPlanId === 3
      ? registrationData.subscriptionSeats || 5
      : 5
  );
  const [customBilling, setCustomBilling] = useState<Billing>(
    registrationData.subscriptionPlanId === 3
      ? (registrationData.subscriptionBilling as Billing)
      : ""
  );

  // Starter/Growth billing
  const handleBillingSwitch = (mode: Billing) => {
    // agar custom select hai aur top tab dabaya → default Starter pe switch
    if (selectedPlanId === null || selectedPlanId === 3) {
      setSelectedPlanId(0); // default Starter
      setBilling(mode);
      const totals = computeTotals("starter", mode);
      setRegistrationData((prev) => ({
        ...prev,
        subscriptionBilling: mode,
        subscriptionPlanId: 0,
        subscriptionSeats: PLAN_META.starter.baseSeats,
        subscriptionCurrency: totals.currency,
        subscriptionTotal: totals.total,
        subscriptionTotalDisplay: totals.display,
      }));
      return;
    }

    // agar Starter/Growth hai
    setBilling(mode);
    const planKey: PlanKey = selectedPlanId === 0 ? "starter" : "growth";
    const totals = computeTotals(planKey, mode);
    setRegistrationData((prev) => ({
      ...prev,
      subscriptionBilling: mode,
      subscriptionPlanId: selectedPlanId,
      subscriptionSeats:
        selectedPlanId === 0
          ? PLAN_META.starter.baseSeats
          : PLAN_META.growth.baseSeats,
      subscriptionCurrency: totals.currency,
      subscriptionTotal: totals.total,
      subscriptionTotalDisplay: totals.display,
    }));
  };

  // Custom billing select
  const handleCustomBillingSelect = (mode: Billing) => {
    setCustomBilling(mode);
    const totals = computeTotals("custom", mode, customSeats);
    setRegistrationData((prev) => ({
      ...prev,
      subscriptionBilling: mode,
      subscriptionPlanId: 3,
      subscriptionSeats: customSeats,
      subscriptionCurrency: totals.currency,
      subscriptionTotal: totals.total,
      subscriptionTotalDisplay: totals.display,
    }));
  };

  const handleSelectPlan = (plan: PlanKey) => {
    if (plan === "custom") {
      setSelectedPlanId(3);
      setCustomBilling("");
      setRegistrationData((prev) => ({
        ...prev,
        subscriptionPlanId: 3,
        subscriptionSeats: customSeats,
        subscriptionBilling: "",
        subscriptionCurrency: "USD",
        subscriptionTotal: 0,
        subscriptionTotalDisplay: "—",
      }));
      return;
    }

    const planId = PLAN_ORDER[plan];
    const seats = PLAN_META[plan].baseSeats;
    const totals = computeTotals(plan, billing);
    setSelectedPlanId(planId);

    setRegistrationData((prev) => ({
      ...prev,
      subscriptionBilling: billing,
      subscriptionPlanId: planId,
      subscriptionSeats: seats,
      subscriptionCurrency: totals.currency,
      subscriptionTotal: totals.total,
      subscriptionTotalDisplay: totals.display,
    }));
  };

  const handleContinue: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (selectedPlanId === null) return;
    if (selectedPlanId === 3 && (!customSeats || !customBilling)) return;
    navigate("/PaymentMethod");
  };

  const PlanCard: React.FC<{ id: "starter" | "growth" }> = ({ id }) => {
    const meta = PLAN_META[id];
    const totals = computeTotals(id, billing);
    const planId = PLAN_ORDER[id];
    const selected = selectedPlanId === planId;

    return (
      <button
        type="button"
        onClick={() => handleSelectPlan(id)}
        className={[
          "relative w-full rounded-2xl sm:px-5 px-3 sm:py-6 py-4 text-left border transition-shadow",
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
          <span className="text-3xl font-bold tracking-tight">
            {money(totals.total)}
          </span>
          <span className="ml-1 text-sm opacity-80">
            {billing === "monthly" ? "/mon" : "/yr"}
          </span>
        </div>

        <div className="mt-2 text-xs opacity-70">
          {billing === "yearly"
            ? "10% off with annual prepayment"
            : `~${money(Math.ceil(meta.monthlyPrice / meta.baseSeats))}/seat baseline`}
        </div>
      </button>
    );
  };

  const PaymentCard: React.FC<{
    type: Billing;
    label: string;
    selected: boolean;
    onClick: () => void;
  }> = ({ label, selected, onClick }) => {
    return (
      <button
        type="button"
        onClick={onClick}
        className={[
          "w-full rounded-xl sm:px-4 px-3 py-3 border text-left transition-all",
          selected
            ? "bg-white border-primary-purple ring-2 ring-primary-purple/30"
            : "bg-white border-primary-blue/20 hover:shadow-sm",
        ].join(" ")}
      >
        <div className="flex items-center justify-between">
          <div className="sm:text-sm text-xs font-semibold text-primary-blue">{label}</div>
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
              total={6}
              onBack={() => navigate(-1)}
            />
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center px-4 sm:mt-0 mt-6">
          <div className="w-full max-w-lg">
            {/* Tabs */}
            <div className="flex items-center gap-6 text-sm font-semibold text-primary-blue mb-3">
              <button
                type="button"
                onClick={() => handleBillingSwitch("monthly")}
                className={`relative pb-2 ${
                  billing === "monthly" && selectedPlanId !== 3
                    ? "text-primary-purple"
                    : "text-primary-blue/70"
                }`}
              >
                Monthly
                {billing === "monthly" && selectedPlanId !== 3 && (
                  <span className="absolute left-0 -bottom-[2px] h-0.5 w-full bg-primary-purple rounded-full" />
                )}
              </button>

              <button
                type="button"
                onClick={() => handleBillingSwitch("yearly")}
                className={`relative pb-2 ${
                  billing === "yearly" && selectedPlanId !== 3
                    ? "text-primary-purple"
                    : "text-primary-blue/70"
                }`}
              >
                Yearly
                {billing === "yearly" && selectedPlanId !== 3 && (
                  <span className="absolute left-0 -bottom-[2px] h-0.5 w-full bg-primary-purple rounded-full" />
                )}
              </button>

              <button
                type="button"
                onClick={() => handleSelectPlan("custom")}
                className={`relative pb-2 ${
                  selectedPlanId === 3 ? "text-primary-purple" : "text-primary-blue/70"
                }`}
              >
                Custom
                {selectedPlanId === 3 && (
                  <span className="absolute left-0 -bottom-[2px] h-0.5 w-full bg-primary-purple rounded-full" />
                )}
              </button>
            </div>

            {/* Custom tab content */}
            {selectedPlanId === 3 && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-primary-blue mb-2 mt-6">
                  Select custom seats
                </h4>
                <label className="block text-xs text-primary-blue/70 mb-1">
                  Per seat: $20
                </label>
                <input
                  type="range"
                  min={5}
                  max={500}
                  step={5}
                  value={customSeats}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setCustomSeats(val);
                    const totals = computeTotals("custom", customBilling, val);
                    setRegistrationData((prev) => ({
                      ...prev,
                      subscriptionSeats: val,
                      subscriptionTotal: totals.total,
                      subscriptionTotalDisplay: totals.display,
                      subscriptionCurrency: totals.currency,
                      subscriptionPlanId: 3,
                      subscriptionBilling: customBilling,
                    }));
                  }}
                  className="w-full accent-primary-purple"
                />
                <div className="flex justify-between text-xs text-primary-blue font-semibold mt-1 mb-6">
                  <span>Seats: {customSeats}</span>
                  <span>
                    Total:{" "}
                    {customBilling === "monthly"
                      ? `$${customSeats * 20}/mon`
                      : customBilling === "yearly"
                      ? `$${customSeats * 20 * 12}/yr`
                      : "—"}
                  </span>
                </div>

                {/* Duration cards */}
                <div className="mt-4">
                  <div className="text-xs text-primary-blue font-semibold mb-2">
                    Duration
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <PaymentCard
                      type="monthly"
                      label="Monthly"
                      selected={customBilling === "monthly"}
                      onClick={() => handleCustomBillingSelect("monthly")}
                    />
                    <PaymentCard
                      type="yearly"
                      label="Yearly"
                      selected={customBilling === "yearly"}
                      onClick={() => handleCustomBillingSelect("yearly")}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Starter/Growth plans */}
            {selectedPlanId !== 3 && (
              <div className="grid grid-cols-2 gap-4">
                <PlanCard id="starter" />
                <PlanCard id="growth" />
              </div>
            )}

            {/* Payment type (always stripe card visible) */}
            <div className="mt-6">
              <div className="text-xs text-primary-blue font-semibold mb-2">
                Payment method
              </div>
              <div className="grid grid-cols-1 gap-3">
                <div className="w-full rounded-xl sm:px-4 px-3 py-3 border bg-white border-primary-purple ring-2 ring-primary-purple/30">
                  <div className="flex items-center justify-between">
                    <div className="sm:text-sm text-xs font-semibold text-primary-blue">
                      Stripe
                    </div>
                    <div className="w-5 h-5 rounded-full border border-primary-purple flex items-center justify-center">
                      <span className="w-2.5 h-2.5 rounded-full bg-primary-purple" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Selection Summary */}
            <div className="mt-6">
              <div className="text-xs text-primary-blue font-semibold mb-2">
                Your selection
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="text-primary-blue/80">Billing</div>
                <div className="text-right text-primary-blue font-semibold">
                  {selectedPlanId === 3 ? customBilling || "—" : billing}
                </div>

                <div className="text-primary-blue/80">Plan</div>
                <div className="text-right text-primary-blue font-semibold">
                  {selectedPlanId === 0
                    ? "Starter"
                    : selectedPlanId === 1
                    ? "Growth"
                    : "Custom"}
                </div>

                <div className="text-primary-blue/80">Seats</div>
                <div className="text-right text-primary-blue font-semibold">
                  {selectedPlanId === 3
                    ? `Custom seats (${customSeats})`
                    : selectedPlanId === null
                    ? "—"
                    : selectedPlanId === 0
                    ? PLAN_META.starter.baseSeats
                    : PLAN_META.growth.baseSeats}
                </div>

                <div className="text-primary-blue/80">Payment</div>
                <div className="text-right text-primary-blue font-semibold">
                  {paymentType}
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
                disabled={
                  selectedPlanId === null ||
                  (selectedPlanId === 3 && (!customSeats || !customBilling))
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPlan;
