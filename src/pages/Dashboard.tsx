// src/screens/Dashboard.tsx
import React from "react";

type Stat = {
  title: string;
  value: string;
  delta: string;
  deltaType: "up" | "down";
};

const deltaClass = (t: Stat["deltaType"]) =>
  t === "up" ? "text-emerald-300" : "text-rose-300";

const Dashboard: React.FC = () => {
  const stats: Stat[] = [
    { title: "Referrals Created", value: "125", delta: "+10%", deltaType: "up" },
    { title: "Referrals Accepted", value: "98", delta: "+5%", deltaType: "up" },
    { title: "Referrals Completed", value: "75", delta: "+8%", deltaType: "up" },
    { title: "Total Points Allocated", value: "$12,500", delta: "+3%", deltaType: "up" },
    { title: "Points Cashed Value", value: "$12,500", delta: "-5%", deltaType: "down" },
    { title: "Missed Referrals", value: "8", delta: "-2%", deltaType: "down" },
  ];

  const activities = [
    "New referral created by Sarah",
    "Referral accepted by David",
    "Referral completed by Emily",
    "Referral completed by Emily",
    "Referral completed by Emily",
    "Referral completed by Emily",
    "Referral completed by Emily",
    "Referral completed by Emily",
  ];

  return (
    <div className="min-h-screen w-full bg-[#F4F6FD]">
      {/* Top bar */}
      <div className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-slate-100">
        <div className="mx-auto max-w-7xl px-3 sm:px-6">
          <div className="h-16 flex items-center justify-between">
            {/* Tabs (left) */}
            <div className="flex items-center gap-2 sm:gap-3">
              <button className="text-[12px] sm:text-sm px-3 py-1.5 rounded-full bg-[#E9E4FF] text-primary-purple font-semibold">
                Dashboard
              </button>
              <button className="hidden sm:inline-block text-sm px-3 py-1.5 rounded-full text-slate-500 hover:bg-slate-100">
                Analytics
              </button>
              <button className="hidden sm:inline-block text-sm px-3 py-1.5 rounded-full text-slate-500 hover:bg-slate-100">
                Team
              </button>
              <button className="hidden sm:inline-block text-sm px-3 py-1.5 rounded-full text-slate-500 hover:bg-slate-100">
                Referral
              </button>
            </div>

            {/* CTAs (right) */}
            <div className="flex items-center gap-2">
              <button className="rounded-full bg-white border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50">
                Generate Report
              </button>
              <button className="rounded-full bg-white border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50">
                Invite Team
              </button>
              <button className="rounded-full bg-[#2CC4F4] text-white px-3 py-1.5 text-sm hover:opacity-90">
                Add Referral
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="mx-auto max-w-7xl px-3 sm:px-6 py-5 grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Main column */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-4">
          {/* Welcome */}
          <div className="rounded-2xl px-4 sm:px-6 py-4 bg-white border border-slate-100">
            <div className="text-slate-500 text-sm">Welcome Back 👋</div>
            <div className="text-primary-blue text-2xl sm:text-3xl font-semibold">
              The Roof Co. Waco <span className="inline-block">👋</span>
            </div>
          </div>

          {/* Stat tiles */}
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
            {stats.map((s) => (
              <div
                key={s.title}
                className="rounded-2xl bg-primary-blue text-white px-4 py-4 shadow-[0_6px_24px_rgba(0,0,0,0.06)]"
              >
                <div className="text-[11px] font-semibold text-white/70 mb-1.5">
                  {s.title}
                </div>
                <div className="text-2xl font-extrabold tracking-tight">{s.value}</div>
                <div className={`mt-2 text-[11px] ${deltaClass(s.deltaType)}`}>{s.delta}</div>
              </div>
            ))}
          </div>

          {/* Referral Trends (placeholder chart area) */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-slate-900">Referral Trends</div>
                <div className="text-emerald-600 text-sm font-semibold mt-1">+15%</div>
                <div className="text-[12px] text-emerald-600">This Week +15%</div>
              </div>

              {/* D/Y/Y toggle (visual only) */}
              <div className="flex items-center gap-4 text-sm">
                <button className="text-slate-400 hover:text-slate-700">D</button>
                <button className="text-slate-400 hover:text-slate-700">Y</button>
                <button className="text-primary-purple font-semibold">Y</button>
              </div>
            </div>

            {/* Chart placeholder — NOT a real chart */}
            <div className="mt-4 rounded-xl border border-slate-200 overflow-hidden">
              <div className="relative h-64 w-full bg-gradient-to-b from-[#CBF0FF] to-[#EAF7FF]">
                {/* soft “waterline” to echo screenshot */}
                <div className="absolute inset-x-0 bottom-0 h-12 bg-white/40" />
                {/* sample tag bubble */}
                <div className="absolute left-1/3 top-10">
                  <span className="px-2 py-1 rounded-full bg-white shadow border border-slate-200 text-[11px] font-semibold text-slate-700">
                    $30.4
                  </span>
                </div>
              </div>
            </div>

            {/* X-axis labels */}
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 px-1">
              <span>Sat</span>
              <span>Sun</span>
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span>Thurs</span>
              <span>Fri</span>
            </div>
          </div>

          {/* Withdrawal Management */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
            <div className="text-sm font-semibold text-slate-900">Withdrawal Management</div>
            <div className="mt-3 text-sm text-slate-500">
              Placeholder section — plug your table or actions here.
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <aside className="lg:col-span-4 xl:col-span-3">
          <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
            <div className="px-4 sm:px-6 py-4">
              <div className="text-sm font-semibold text-slate-900">Recent Activity</div>
            </div>

            <div className="flex">
              {/* purple rail */}
              <div className="w-1 bg-primary-purple rounded-r-lg ml-4 sm:ml-6" />
              <ul className="flex-1 px-4 sm:px-6 py-2 space-y-5">
                {activities.map((a, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="mt-[7px] h-2 w-2 rounded-full bg-primary-purple" />
                    <div className="flex-1">
                      <div className="text-sm text-slate-800">{a}</div>
                      <div className="text-[11px] text-slate-500">2 hours ago</div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Spacer card */}
          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
            <div className="text-sm font-semibold text-slate-900">Notes</div>
            <p className="mt-2 text-sm text-slate-500">
              Add announcements, alerts, or quick links here.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default Dashboard;
