import React from "react";

interface ButtonProps {
  text: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  py?: string;                 // e.g. "py-2 sm:py-3"
  px?: string;                 // e.g. "px-6"
  fullWidth?: boolean;         // <- NEW (defaults to true)
  mt?: string;                 // <- optional margin-top, default "mt-6"
  className?: string;
}

const Button: React.FC<ButtonProps> = ({
  text,
  onClick,
  disabled = false,
  py,
  px,
  fullWidth = true,            // keep old behavior
  mt = "mt-6",
  className = "",
}) => {
  const base =
    "inline-flex items-center justify-center rounded-full text-primary-blue text-sm font-semibold " +
    "shadow-[0_10px_30px_rgba(0,0,0,0.12)] bg-secondary-blue transition " +
    "hover:shadow-[0_12px_36px_rgba(0,0,0,0.15)] hover:scale-[102%] duration-300 " +
    "disabled:opacity-60 disabled:cursor-not-allowed text-nowrap";

  const paddingY = py ?? "py-4 sm:py-5";
  const paddingX = px ?? "px-6";
  const width    = fullWidth ? "w-full" : "w-auto";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${mt} ${paddingY} ${paddingX} ${width} ${className}`.trim()}
    >
      {text}
    </button>
  );
};

export default Button;
