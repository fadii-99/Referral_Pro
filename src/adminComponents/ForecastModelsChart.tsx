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

const ForecastModelsChart: React.FC = () => {
  const data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    datasets: [
      {
        label: "Forecast",
        data: [120, 150, 100, 200, 180, 220, 250, 300],
        borderColor: "#00C4F4",
        backgroundColor: (ctx: any) => {
          const { ctx: chartCtx, chartArea } = ctx.chart;
          if (!chartArea) return "rgba(0,196,244,0.3)";
          const gradient = chartCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, "rgba(0,196,244,0.45)");
          gradient.addColorStop(1, "rgba(0,196,244,0.06)");
          return gradient;
        },
        pointBackgroundColor: "#fff",
        pointBorderColor: "#00C4F4",
        pointBorderWidth: 2,
        pointRadius: 4.5,
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
        callbacks: { title: () => "", label: (ctx: any) => `$${ctx.parsed.y}` },
      },
    },
    scales: {
      y: { beginAtZero: true, grid: { display: false }, ticks: { display: false } },
      x: {
        grid: { display: false },
        border: { display: true, color: "rgba(0,196,244,0.35)", width: 2 },
        ticks: { color: "#0b0d3b", font: { weight: "700" as const } },
      },
    },
  };

  return (
    <div className="bg-white md:p-6 p-4 rounded-xl shadow-sm">
      <h3 className="sm:text-xl text-md font-semibold text-primary-blue mb-2">Forecast Models</h3>
      <div className="mb-8">
        <span className="font-bold sm:text-4xl text-2xl text-primary-blue">$150,000</span>
        <p className="sm:text-sm text-[10px] text-primary-blue">
          Next Month <span className="text-green-500">+20%</span>
        </p>
      </div>
      <div className="h-[25rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default ForecastModelsChart;
