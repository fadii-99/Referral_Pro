import React, { useMemo } from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
} from "chart.js";
import ChartDataLabels from "chartjs-plugin-datalabels";

ChartJS.register(ArcElement, Tooltip, ChartDataLabels);

type Props = {
  accepted?: number; // e.g., 45
  rejected?: number; // e.g., 35
  pending?: number;  // e.g., 20
  className?: string;
};

const AnalyticsPieChart: React.FC<Props> = ({
  accepted = 45,
  rejected = 35,
  pending  = 20,
}) => {
  // Colors like your screenshot
  const C_TEAL_DARK = "#11A8A2"; // dark teal
  const C_ORANGE    = "#F98C4A"; // orange
  const C_TEAL_LT   = "#C8EBEA"; // light teal
  const COLORS = [C_TEAL_LT, C_TEAL_DARK, C_ORANGE]; // order to resemble ref

  
  // Decide label color (white on dark slices, navy on light slice)
  const isLightHex = (hex: string) => {
    const v = hex.replace("#", "");
    const r = parseInt(v.substring(0, 2), 16);
    const g = parseInt(v.substring(2, 4), 16);
    const b = parseInt(v.substring(4, 6), 16);
    // luminance heuristic
    return (0.299 * r + 0.587 * g + 0.114 * b) > 180;
  };

  const DATA = useMemo(() => {
    const labels = ["Accepted", "Rejected", "Pending"];
    const raw = [accepted, rejected, pending];

    return {
      labels,
      datasets: [
        {
          data: raw,
          backgroundColor: COLORS,
          borderColor: "#FFFFFF",
          borderWidth: 8,        // thick white separators
          hoverOffset: 6,
          spacing: 0,
        },
      ],
    };
  }, [accepted, rejected, pending]);

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }, // keep it clean like the reference
      tooltip: {
        displayColors: true,
        callbacks: {
          label: (ctx: any) => ` ${ctx.label}: ${ctx.parsed}`,
        },
      },
      datalabels: {
        formatter: (value: number, ctx: any) => {
          const sum = ctx.chart.data.datasets[0].data.reduce(
            (a: number, b: number) => a + b,
            0
          );
          const p = Math.round((value / sum) * 100);
          return p > 0 ? `${p}%` : "";
        },
        color: (ctx: any) => {
          const bg = ctx.dataset.backgroundColor[ctx.dataIndex] as string;
          return isLightHex(bg) ? "#0B0D3B" : "#FFFFFF";
        },
        font: { weight: "700", size: 14 },
        anchor: "center",
        align: "center",
        clamp: true,
        clip: false,
      },
    },
    rotation: -0.1,  // tiny offset so a seam isn't dead-vertical (aesthetic)
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-black/5 p-5">
      <div className="mb-4">
        <p className="text-sm text-slate-600">Earnings by Business</p>
        <div className="text-2xl font-bold text-primary-blue leading-tight">+10%</div>
        <p className="text-sm text-slate-600">
          This Month <span className="text-green-500">+10%</span>
        </p>
      </div>


      <div className="flex items-center justify-center gap-8 mb-4 w-full">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_TEAL_LT }} />
          <span className="text-slate-700 text-sm">Accepted</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_TEAL_DARK }} />
          <span className="text-slate-700 text-sm">Rejected</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_ORANGE }} />
          <span className="text-slate-700 text-sm">Pending</span>
        </div>
      </div>
     

      {/* Pie chart */}
    <div className="h-full w-full">
  <Pie data={DATA} options={options} />
</div>



    </div>
  );
};

export default AnalyticsPieChart;
