import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend,
} from "chart.js";
import ChartDataLabels from "chartjs-plugin-datalabels";

// Register basic chart components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend
);

// ❌ make sure datalabels not auto-activated
ChartJS.unregister(ChartDataLabels);

const ReferralTrendsChart: React.FC = () => {
  // Brand colors
  const lineColor = "#00C4F4";
  const topFill = "rgba(0, 196, 244, 0.45)";
  const bottomFill = "rgba(0, 196, 244, 0.06)";

  // Gradient fill
  const gradientBg = (context: any) => {
    const { ctx, chartArea } = context.chart;
    if (!chartArea) return topFill;
    const gradient = ctx.createLinearGradient(
      0,
      chartArea.top,
      0,
      chartArea.bottom
    );
    gradient.addColorStop(0, topFill);
    gradient.addColorStop(1, bottomFill);
    return gradient;
  };

  const data = {
    labels: ["Sat", "Sun", "Mon", "Tue", "Wed", "Thurs", "Fri"],
    datasets: [
      {
        label: "Referral Trends",
        data: [22, 34, 27, 39, 19, 36, 52],
        borderColor: lineColor,
        backgroundColor: gradientBg,
        pointBackgroundColor: "#fff",
        pointBorderColor: lineColor,
        pointBorderWidth: 2,
        pointRadius: 4.5,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.45,
        borderWidth: 3,
      },
    ],
  };

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        intersect: false,
        displayColors: false,
        padding: 10,
        backgroundColor: "#0ea5e9",
        titleColor: "#fff",
        bodyColor: "#fff",
        callbacks: {
          title: () => "",
          label: (ctx: any) => `$${ctx.parsed.y}`,
        },
      },
      datalabels: {
        display: false, // 🚀 disables permanent numbers
      },
    },
    elements: {
      point: { hitRadius: 16 },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { display: false, drawBorder: false },
        ticks: { display: false },
      },
      x: {
        grid: { display: false },
        border: {
          display: true,
          color: "rgba(0, 196, 244, 0.35)",
          width: 2,
        },
        ticks: {
          color: "#0b0d3b",
          font: { weight: "700" as const },
        },
      },
    },
  };

  return (
    <div className="bg-white md:p-6 p-4 rounded-xl shadow-sm">
      <h3 className="sm:text-xl text-md font-semibold text-primary-blue md:mb-4 mb-2">
        Referral Trends
      </h3>
      <div className="mb-4">
        <span className="font-bold sm:text-4xl text-2xl text-primary-blue">
          +15%
        </span>
        <p className="sm:text-sm text-[10px] text-primary-blue">
          This Week <span className="text-green-500">+15%</span>
        </p>
      </div>
      <div className="h-[25rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default ReferralTrendsChart;
