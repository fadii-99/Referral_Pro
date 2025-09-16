import React from "react";
import { PulseLoader } from "react-spinners";

const SmallLoader: React.FC<{ color?: string }> = ({ color = "#6d28d9" }) => {
  return <PulseLoader size={6} color={color} />;
};

export default SmallLoader;
