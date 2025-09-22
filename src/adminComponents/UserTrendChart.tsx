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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend
);

const UserTrendChart: React.FC = () => {
  const lineColor = "#00C4F4";
  const topFill = "rgba(0, 196, 244, 0.45)";
  const bottomFill = "rgba(0, 196, 244, 0.06)";

  const gradientBg = (context: any) => {
    const { ctx, chartArea } = context.chart;
    if (!chartArea) return topFill;
    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    gradient.addColorStop(0, topFill);
    gradient.addColorStop(1, bottomFill);
    return gradient;
  };

  const data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
    datasets: [
      {
        label: "Active Users",
        data: [1200, 1400, 1350, 1600, 1800, 1750, 2000],
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
          label: (ctx: any) => `${ctx.parsed.y} users`,
        },
      },
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
      <h3 className="sm:text-2xl text-lg font-semibold text-primary-blue mb-6">
        Active Users Trend
      </h3>
      <div className="h-[25rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default UserTrendChart;
