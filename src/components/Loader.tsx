import React from "react";
import logo from "./../assets/referralProLogo.png";


const Loader: React.FC<{ fullscreen?: boolean; label?: string }> = ({
  fullscreen = true,
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
      <img
        src={logo}
        alt="Loader Logo"
        className="h-10 w-auto animate-fadeInOut"
      />
      {/* <p className="mt-6 text-primary-blue font-semibold text-sm ">
        {label}
      </p> */}
    </Wrapper>
  );
};

export default Loader;
