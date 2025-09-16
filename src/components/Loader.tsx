import React from "react";
import { HashLoader } from "react-spinners";

const Loader: React.FC<{ fullscreen?: boolean; label?: string }> = ({
  fullscreen = true,
  label = "Loading…",
}) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <div
      className={[
        fullscreen ? "fixed inset-0" : "w-full h-full",
        "z-[999] flex flex-col items-center justify-center bg-white/70 backdrop-blur-sm",
      ].join(" ")}
    >
      {children}
    </div>
  );

  return (
    <Wrapper>
      <HashLoader size={80} color="#02025c" speedMultiplier={1.3} />
      <p className="mt-6 text-primary-blue font-semibold text-sm animate-pulse">
        {label}
      </p>
    </Wrapper>
  );
};

export default Loader;
