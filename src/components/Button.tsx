import React from "react";

interface ButtonProps {
  text: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>; // ✅ universal handler type
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ text, onClick, disabled = false }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="mt-6 w-full rounded-full py-5 text-primary-blue text-sm font-semibold
                 shadow-[0_10px_30px_rgba(0,0,0,0.12)] bg-secondary-blue transition
                 hover:shadow-[0_12px_36px_rgba(0,0,0,0.15)] hover:scale-[102%] duration-300
                 disabled:opacity-60 disabled:cursor-not-allowed"
    >
      {text}
    </button>
  );
};

export default Button;
