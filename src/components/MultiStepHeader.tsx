import React from "react";


type Props = {
  title: string;
  current: number;  
  total: number;   
  onBack?: () => void;
  className?: string;
};



const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));


const MultiStepHeader: React.FC<Props> = ({ title, current, total, onBack, className }) => {
  const cur = clamp(current, 1, total);



  return (
    <header className={`w-full ${className ?? ""}`}>
     <div className="flex justify-center w-full">
        <ul className="flex items-center gap-2 w-full">
            {Array.from({ length: total }).map((_, i) => {
            const stepIndex = i + 1;
            const isDone = stepIndex < cur;
            const isActive = stepIndex === cur;
            return (
                <li
                key={i}
                className={[
                    "h-1 flex-1 rounded-full transition-colors", // 🔹 flex-1 instead of w-14
                    isDone ? "bg-primary-purple" :
                    isActive ? "bg-primary-purple/70" :
                    "bg-gray-300/60"
                ].join(" ")}
                />
            );
            })}
        </ul>
        </div>


      <div className="mt-4 flex flex-row items-center justify-between">
        <div className="justify-self-start ">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-1 text-primary-blue/80 hover:text-primary-blue transition disabled:opacity-40"
            aria-label="Go back"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            <span className="sr-only">Back</span>
          </button>
        </div>

        <div className="flex flex-col items-end w-full">
            <span className="justify-self-end text-xs md:text-sm text-gray-500 mb-1">
            {cur}/{total}
            </span>
             <h2 className="justify-self-center text-sm md:text-base font-semibold text-primary-blue">
            {title}
            </h2>
        </div>
      </div>
    </header>
  );
};

export default MultiStepHeader;
