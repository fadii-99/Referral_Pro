import React, { useState } from "react";

type Request = {
  id: string;
  user: string;
  compliance: "Compliant" | "Non-Compliant";
  amount: string;
  method: string;
};

const dummy: Request[] = [
  { id: "1", user: "Alice Johnson", compliance: "Compliant", amount: "$150", method: "PayPal" },
  { id: "2", user: "Bob Williams", compliance: "Non-Compliant", amount: "$150", method: "Bank Transfer" },
  { id: "3", user: "Alice Johnson", compliance: "Compliant", amount: "$150", method: "PayPal" },
  { id: "4", user: "Alice Johnson", compliance: "Compliant", amount: "$150", method: "PayPal" },
  { id: "5", user: "Alice Johnson", compliance: "Compliant", amount: "$150", method: "PayPal" },
];

const Pill: React.FC<{ label: string; type: "Compliant" | "Non-Compliant" }> = ({
  label,
  type,
}) => {
  const map: Record<string, string> = {
    Compliant: "text-primary-purple bg-primary-purple/10",
    "Non-Compliant": "text-rose-600 bg-rose-100",
  };
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium ${map[type]}`}
    >
      {label}
    </span>
  );
};

const WithdrawalManagement: React.FC = () => {
  const [tab, setTab] = useState<"pending" | "history">("pending");

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 md:p-6 p-4">
      <h3 className="text-lg font-semibold text-primary-blue mb-6">Withdrawal Management</h3>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-gray-200 mb-4">
        <button
          className={`pb-2 md:text-sm text-xs font-semibold ${
            tab === "pending"
              ? "text-primary-purple border-b-2 border-primary-purple"
              : "text-gray-400"
          }`}
          onClick={() => setTab("pending")}
        >
          Pending Request
        </button>
        <button
          className={`pb-2 md:text-sm text-xs font-semibold ${
            tab === "history"
              ? "text-primary-purple border-b-2 border-primary-purple"
              : "text-gray-400"
          }`}
          onClick={() => setTab("history")}
        >
          History
        </button>
      </div>

      {tab === "pending" ? (
        <div className="overflow-x-auto">
          <table className="w-full md:text-sm text-xs text-left">
            <thead>
              <tr className="text-gray-500 font-semibold">
                <th className="px-4 py-2 text-nowrap">User Name</th>
                <th className="px-4 py-2 text-nowrap">Tax Compliance</th>
                <th className="px-4 py-2 text-nowrap">Amount</th>
                <th className="px-4 py-2 text-nowrap">Payment Method</th>
                <th className="px-4 py-2 text-nowrap">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {dummy.map((req) => (
                <tr key={req.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-nowrap text-gray-800">{req.user}</td>
                  <td className="px-4 py-3 text-nowrap">
                    <Pill label={req.compliance} type={req.compliance} />
                  </td>
                  <td className="px-4 py-3 text-nowrap text-gray-700">{req.amount}</td>
                  <td className="px-4 py-3 text-nowrap text-gray-700">{req.method}</td>
                  <td className="px-4 py-3 text-nowrap text-primary-purple font-medium space-x-2 text-nowrap">
                    <button className="hover:underline">Approve</button>
                    <span>/</span>
                    <button className="hover:underline">Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-6 md:text-sm text-xs text-gray-500">No history yet.</div>
      )}
    </div>
  );
};

export default WithdrawalManagement;
