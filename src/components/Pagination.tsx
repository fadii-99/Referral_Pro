import React from "react";

type Props = {
  current: number;
  totalPages: number;
  onChange: (page: number) => void;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
};

const Pagination: React.FC<Props> = ({ current, totalPages, onChange, prefix, suffix }) => {
  // windowed pages: 1 … 3 4 [5] 6 7 … N
  const pages = (): (number | "...")[] => {
    const out: (number | "...")[] = [];
    const windowSize = 2;

    out.push(1);
    const start = Math.max(2, current - windowSize);
    const end = Math.min(totalPages - 1, current + windowSize);

    if (start > 2) out.push("...");
    for (let i = start; i <= end; i++) out.push(i);
    if (end < totalPages - 1) out.push("...");
    if (totalPages > 1) out.push(totalPages);

    return out;
  };

  return (
    <div className="flex items-center gap-2">
      {prefix}

      <div className="flex items-center gap-1">
        {pages().map((p, idx) =>
          p === "..." ? (
            <span key={`dots-${idx}`} className="px-2 text-slate-400">…</span>
          ) : (
            <button
              key={p}
              type="button"
              aria-current={p === current ? "page" : undefined}
              onClick={() => onChange(p)}
              className={[
                "h-9 w-9 rounded-lg border border-black/5 text-xs",
                p === current
                  ? "bg-[#0b0d3b] text-white"
                  : "bg-white text-slate-700 hover:bg-slate-50",
              ].join(" ")}
            >
              {p}
            </button>
          )
        )}
      </div>

      {suffix}
    </div>
  );
};

export default Pagination;
