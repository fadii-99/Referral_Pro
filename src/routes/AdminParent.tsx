import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";

const AdminParent: React.FC = () => {
  return (
    <div className="w-full max-h-screen">
      <Navbar />
      <div>
        <Outlet />
      </div>
    </div>
  );
};

export default AdminParent;
