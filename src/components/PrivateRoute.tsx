import React, { useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

const PrivateRoute: React.FC = () => {
  const token = localStorage.getItem("accessToken");
  const [showModal, setShowModal] = useState(!token);

  if (!token) {
    return (
      <>
        {/* Redirect after closing modal */}
        {!showModal && <Navigate to="/Login" replace />}

        {/* Tailwind Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
              <h2 className="text-lg font-semibold text-primary-blue">
                Authentication Required
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                Kindly login to continue.
              </p>
              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm rounded-lg bg-primary-purple text-white hover:bg-primary-purple/90 transition"
                >
                  Go to Login
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // ✅ Agar token hai → show nested routes
  return <Outlet />;
};

export default PrivateRoute;
