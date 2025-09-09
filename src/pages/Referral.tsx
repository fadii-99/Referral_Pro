import React, { useEffect, useState } from "react";
import { FiFilter, FiSliders } from "react-icons/fi";
import Pagination from "../components/Pagination";
import ReferralRow from "../components/ReferralRow";
import type { Referral } from "../components/ReferralRow";
import { useReferralContext } from "../context/ReferralProvider";

const Referral: React.FC = () => {
  const { referrals, loading, error } = useReferralContext();
  const [page, setPage] = useState(1);

  // console log for debugging
  useEffect(() => {
    console.log("[Referral page] referrals:", referrals);
  }, [referrals]);

  const rowsPerPage = 8;
  const totalPages = Math.max(1, Math.ceil(referrals.length / rowsPerPage));
  const start = (page - 1) * rowsPerPage;
  const current = referrals.slice(start, start + rowsPerPage);

  // keep page valid if data length shrinks
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [totalPages, page]);

  return (
    <div className="p-6 flex flex-col min-h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between pb-4">
        <h2 className="text-2xl font-semibold text-primary-blue">
          Company Referrals List
        </h2>
        <div className="flex flex-row items-center gap-3">
          <button className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center">
            <FiFilter className="text-primary-purple text-lg" />
          </button>
          <button className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center">
            <FiSliders className="text-primary-purple text-lg" />
          </button>
        </div>
      </div>

      {/* Loading/Error */}
      {loading && <p className="text-sm text-gray-600">Loading referrals...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Table */}
      <div className="flex-1 flex flex-col space-y-4">
        {/* Header */}
        <div className="grid grid-cols-[0.6fr_2fr_1.5fr_1.5fr_1.2fr_1fr] px-6 py-3 text-xs sm:text-sm font-semibold text-gray-600 bg-gray-50 rounded-xl">
          <div>ID</div>
          <div>Company Name</div>
          <div>Industry</div>
          <div>Company Type</div>
          <div>Status</div>
          <div>Urgency</div>
        </div>

        {/* Rows */}
        <div className="space-y-2">
          {current.length === 0 && !loading ? (
            <div className="text-sm p-8 text-center text-gray-500">
              No referrals found.
            </div>
          ) : (
            current.map((r: Referral) => (
              <ReferralRow key={r.id} referral={r} />
            ))
          )}
        </div>
      </div>

      {/* Pagination */}
      {current.length > 0 && !loading && (
        <div className="mt-auto pt-6 flex justify-end">
          <Pagination
            current={page}
            totalPages={totalPages}
            onChange={(p) => setPage(p)}
          />
        </div>
      )}
    </div>
  );
};

export default Referral;
