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
  accepted?: number;
  rejected?: number;
  pending?: number;
  className?: string;
};

const AnalyticsPieChart: React.FC<Props> = ({
  accepted = 45,
  rejected = 35,
  pending  = 20,
}) => {
  // Theme colors
  const C_BLUE_LT  = "#f1eff9"; // primary-gray (lightest)
  const C_BLUE     = "#02025c"; // primary-blue (dark navy)
  const C_PURPLE   = "#7c5af6"; // primary-purple
  const COLORS = [C_BLUE_LT, C_BLUE, C_PURPLE];

  // Decide label color (white on dark slices, navy on light slice)
  const isLightHex = (hex: string) => {
    const v = hex.replace("#", "");
    const r = parseInt(v.substring(0, 2), 16);
    const g = parseInt(v.substring(2, 4), 16);
    const b = parseInt(v.substring(4, 6), 16);
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
          borderWidth: 8,
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
      legend: { display: false },
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
          return isLightHex(bg) ? "#02025c" : "#FFFFFF"; // navy on light, white on dark
        },
        font: { weight: "700", size: 14 },
        anchor: "center",
        align: "center",
        clamp: true,
        clip: false,
      },
    },
    rotation: -0.1,
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-black/5 md:p-5 p-3 h-full flex flex-col"> 
      <h3 className="sm:text-xl text-md font-semibold text-primary-blue md:mb-4 mb-2">
        Earnings by Business
      </h3>
      <div className="mb-4">
        <span className="font-bold sm:text-4xl text-2xl text-primary-blue">
          +10%
        </span>
        <p className="sm:text-sm text-[10px] text-primary-blue">
          This Month <span className="text-green-500">+10%</span>
        </p>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-8 mb-4">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_BLUE_LT }} />
          <span className="text-slate-700 md:text-sm text-xs">Accepted</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_BLUE }} />
          <span className="text-slate-700 md:text-sm text-xs">Rejected</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: C_PURPLE }} />
          <span className="text-slate-700 md:text-sm text-xs">Pending</span>
        </div>
      </div>

      {/* Pie chart */}
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full h-full">
          <Pie data={DATA} options={options} />
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPieChart;
