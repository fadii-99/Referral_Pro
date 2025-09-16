import React, { useEffect, useState, useCallback } from "react";
import Button from "../components/Button";
import SmallLoader from "../components/SmallLoader";
import { HiMail, HiPhone, HiChevronDown } from "react-icons/hi";
import { useTeamMembersContext } from "../context/TeamMembersProvider";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const serverUrl = import.meta.env.VITE_SERVER_URL;

type ReferralDetailType = {
  id: number;
  reference_id: string;
  company_name: string;
  company_type: string;
  industry: string;
  status: string;
  urgency: string;
  approval: string;
  assigned_at: string;
  assigned_notes: string;
  assigned_to_id: number | null;
  assigned_to_name: string;
  referred_to_name: string;
  referred_to_email: string;
  referred_to_phone: string;
  notes: string;
  reason: string;
  date: string;
  privacy: boolean;
};

const ReferralDetail: React.FC = () => {
  const [detail, setDetail] = useState<ReferralDetailType | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const { membersFromApi, loading: teamLoading } = useTeamMembersContext();
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const [status, setStatus] = useState("Accept");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchDetail = useCallback(async () => {
    const token = localStorage.getItem("accessToken");
    const referralId = localStorage.getItem("selectedReferralId");


    try {
      setLoadingDetail(true);
      const res = await fetch(`${serverUrl}/refer/list_company_referral/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ referral_id: referralId }),
      });


      const data = await res.json();
      const detailData = Array.isArray(data.referrals)
        ? data.referrals[0]
        : null;

      setDetail(detailData);
    } catch (err) {
      // console.error("Error fetching referral detail:", err);
      toast.error("⚠️ Failed to load referral detail");
    } finally {
      setLoadingDetail(false);
    }
  }, []);


  useEffect(() => {
    void fetchDetail();
  }, [fetchDetail]);

  const handleStatusUpdate = async () => {
    if (!detail) return;

    if (!selectedEmployee && status !== "Reject") {
      toast.error("⚠️ Please select an employee before proceeding.");
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem("accessToken");
      const res = await fetch(`${serverUrl}/refer/assign_rep/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          referral_id: detail.id,
          status,
          employee_id: status === "Reject" ? null : selectedEmployee?.id,
          note: note || "",
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        toast.error(`Failed: ${res.status} - ${errText}`);
        return;
      }

      const response = await res.json();
      toast.success("✅ Status updated successfully!");
      console.log("Status update response:", response);

      await fetchDetail();
    } catch (err) {
      // console.error("Status update error:", err);
      toast.error("Network error, please try again");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingDetail || !detail) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <SmallLoader />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 flex flex-col min-h-screen space-y-6">
      {/* Heading */}
      <h2 className="text-xl sm:text-2xl font-semibold text-primary-blue text-center sm:text-left">
        Referral Details
      </h2>

      {/* Top Card */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6">
        <div className="flex flex-col items-start gap-1 sm:gap-2">
          <p className="text-xs text-gray-500">Reference ID</p>
          <p className="font-semibold text-primary-blue text-sm sm:text-base">
            #{detail.reference_id}
          </p>
        </div>
        <div className="text-left sm:text-right mt-3 sm:mt-0 flex flex-col items-start sm:items-end">
          <p className="text-xs text-gray-500">{detail.date}</p>
          <span className="inline-flex items-center px-2 sm:px-3 py-1 rounded-lg text-xs font-medium text-amber-500 bg-amber-50 mt-2">
            {detail.status}
          </span>
        </div>
      </div>

      {/* Customer Info */}
      <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-primary-blue mb-4">
          Customer Info
        </h3>
        <div className="flex flex-col sm:flex-row sm:justify-between items-start sm:items-center gap-4">
          <div className="flex items-start gap-3 sm:gap-4">
            <img
              src={`https://ui-avatars.com/api/?name=${encodeURIComponent(
                detail.referred_to_name || "User"
              )}&background=E5E7EB&color=374151`}
              alt={detail.referred_to_name}
              className="h-10 w-10 sm:h-12 sm:w-12 rounded-full object-cover"
            />
            <div className="flex flex-col gap-2">
              <p className="font-medium text-primary-blue text-sm sm:text-base">
                {detail.referred_to_name}
              </p>
              <p className="text-xs text-gray-600 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 pb-2">
                <span
                  className={`flex items-center gap-1 ${
                    detail.privacy ? "blur-sm select-none" : ""
                  }`}
                >
                  <HiMail className="text-gray-500 text-sm" />
                  {detail.referred_to_email}
                </span>
                <span
                  className={`flex items-center gap-1 ${
                    detail.privacy ? "blur-sm select-none" : ""
                  }`}
                >
                  <HiPhone className="text-gray-500" />
                  {detail.referred_to_phone}
                </span>
              </p>
              <p className="text-xs text-gray-600">
                <span className="font-semibold">Reason:</span> {detail.reason}
              </p>
              <p className="text-xs text-gray-600">
                <span className="font-semibold">Notes:</span> {detail.notes}
              </p>
            </div>
          </div>
          <div>
            <span
              className={`inline-flex items-center px-2 sm:px-3 py-1 rounded-lg text-xs font-medium capitalize
                ${
                  detail.urgency?.toLowerCase() === "urgent"
                    ? "text-rose-500 bg-rose-50"
                    : detail.urgency?.toLowerCase() === "normal"
                    ? "text-blue-500 bg-blue-50"
                    : "text-slate-500 bg-slate-50"
                }`}
            >
              {detail.urgency}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {!detail.assigned_to_id ? (
          <>
            {/* Assignment */}
            <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-primary-blue mb-4">
                Assignment
              </h3>
              <div className="relative">
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm sm:text-base text-left focus:outline-none focus:ring-2 focus:ring-primary-purple flex justify-between items-center"
                >
                  {selectedEmployee ? selectedEmployee.name : "Select Employee"}
                  <HiChevronDown className="text-gray-400" />
                </button>

                {dropdownOpen && (
                  <div className="absolute z-20 mt-2 w-full bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto">
                    {teamLoading ? (
                      <div className="p-4 text-center text-gray-500 text-sm">
                        Loading...
                      </div>
                    ) : membersFromApi.length === 0 ? (
                      <div className="p-4 text-center text-gray-500 text-sm">
                        No team members found
                      </div>
                    ) : (
                      membersFromApi.map((member) => (
                        <div
                          key={member.id}
                          onClick={() => {
                            setSelectedEmployee(member);
                            setDropdownOpen(false);
                          }}
                          className="flex items-center gap-3 px-4 py-2 cursor-pointer hover:bg-gray-50"
                        >
                          <img
                            src={member.avatar}
                            alt={member.name}
                            className="h-8 w-8 rounded-full"
                          />
                          <div>
                            <p className="text-sm font-medium text-primary-blue">
                              {member.name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {member.email}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {selectedEmployee && (
                <div className="mt-5 flex items-center gap-3 p-3 border border-gray-100 rounded-xl bg-gray-50">
                  <img
                    src={selectedEmployee.avatar}
                    alt={selectedEmployee.name}
                    className="h-8 w-8 sm:h-10 sm:w-10 rounded-full"
                  />
                  <div>
                    <p className="text-sm font-medium text-primary-blue">
                      {selectedEmployee.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {selectedEmployee.email}
                    </p>
                  </div>
                </div>
              )}
              <p className="text-xs text-gray-500 mt-3">
                ⚠️ Only one employee can be assigned.
              </p>
            </div>

            {/* Status Update */}
            <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold text-primary-blue mb-4">
                Status Update
              </h3>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-primary-purple"
              >
                <option>Accept</option>
                <option>Reject</option>
                <option>In Progress</option>
              </select>

              <h4 className="text-sm font-semibold text-primary-blue mt-5">
                Note
              </h4>
              <textarea
                placeholder="Write here..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="w-full mt-2 border border-gray-200 rounded-xl px-3 py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-primary-purple"
                rows={4}
              />

              <div className="flex justify-end mt-4">
                <Button
                  text={submitting ? "Submitting..." : "Done"}
                  onClick={handleStatusUpdate}
                  disabled={!selectedEmployee}
                />
              </div>
            </div>
          </>
        ) : (
          /* Already Assigned */
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6 lg:col-span-2">
            <h3 className="text-base sm:text-lg font-semibold text-primary-blue mb-4">
              Assigned Info
            </h3>
            <div className="flex flex-col gap-4 mt-6">
              <div>
                <p className="text-xs text-gray-500">Assigned To</p>
                <p className="text-sm sm:text-base font-semibold text-primary-blue">
                  {detail.assigned_to_name}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Assigned Date</p>
                <p className="text-sm sm:text-base text-primary-blue font-semibold">
                  {detail.assigned_at}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Notes</p>
                <p className="text-xs sm:text-sm text-gray-700">
                  {detail.assigned_notes || "—"}
                </p>
              </div>
            </div>
          </div>
        )}

       {/* Activity Log */}
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-black/5 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-primary-blue mb-4">
            Activity Log
          </h3>
          <div className="relative pl-6">
            <div className="absolute left-[7px] top-0 bottom-0 w-px bg-gray-200"></div>
            <div className="space-y-6">
              <div className="relative">
                <span className="absolute -left-[22px] top-1 h-3 w-3 rounded-full bg-emerald-500"></span>
                <p className="text-xs text-gray-500">Sep 07, 2025</p>
                <p className="text-primary-blue font-medium text-sm">
                  Referral received from <span className="font-semibold">Ali Kazmi</span>
                </p>
                <p className="text-xs text-gray-500">10:15 AM</p>
              </div>
              <div className="relative">
                <span className="absolute -left-[22px] top-1 h-3 w-3 rounded-full bg-emerald-500"></span>
                <p className="text-xs text-gray-500">Sep 08, 2025</p>
                <p className="text-primary-blue font-medium text-sm">
                  Assigned to <span className="font-semibold">Usama Kamran</span>
                </p>
                <p className="text-xs text-gray-500">02:30 PM</p>
              </div>
              <div className="relative">
                <span className="absolute -left-[22px] top-1 h-3 w-3 rounded-full bg-emerald-500"></span>
                <p className="text-xs text-gray-500">Sep 09, 2025</p>
                <p className="text-primary-blue font-medium text-sm">
                  Follow-up updated by <span className="font-semibold">Fawad</span>
                </p>
                <p className="text-xs text-gray-500">11:00 AM</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />
    </div>
  );
};

export default ReferralDetail;
