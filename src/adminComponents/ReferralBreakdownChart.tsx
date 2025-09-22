import React from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const ReferralBreakdownChart: React.FC = () => {
  const data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"], // 7 bars
    datasets: [
      {
        label: "Referrals",
        data: [150, 200, 250, 220, 300, 270, 310],
        backgroundColor: [
          "#0b0d3b", // dark blue
          "#00C4F4", // light blue
          "#0b0d3b",
          "#00C4F4",
          "#0b0d3b",
          "#00C4F4",
          "#0b0d3b",
        ],
        borderRadius: 12,
      },
    ],
  };

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#0ea5e9",
        titleColor: "#fff",
        bodyColor: "#fff",
        callbacks: {
          label: (ctx: any) => `${ctx.parsed.y} referrals`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { display: false, drawBorder: false }, // no horizontal lines
        ticks: { display: false },
      },
      x: {
        grid: { display: false }, // no vertical lines
        border: {
          display: true,
          color: "rgba(0, 196, 244, 0.35)", // only bottom axis line
          width: 2,
        },
        ticks: {
          color: "#0b0d3b",
          font: { weight: "600" as const },
        },
      },
    },
  };

  return (
    <div className="bg-white md:p-6 p-4 rounded-xl shadow-sm">
      <h3 className="sm:text-2xl text-lg font-semibold text-primary-blue mb-6">
        Referral Breakdown
      </h3>
      <div className="h-[25rem]">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

export default ReferralBreakdownChart;
