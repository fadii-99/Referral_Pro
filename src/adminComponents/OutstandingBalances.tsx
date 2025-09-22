import React from "react";

const OutstandingBalances: React.FC = () => {
  const rows = [
    { id: 1, company: "Acme Corp", status: "Overdue", amount: "$150", due: "June 15, 2024" },
    { id: 2, company: "Gamma Ltd", status: "Completed", amount: "$150", due: "June 15, 2024" },
    { id: 3, company: "Gamma Ltd", status: "Pending", amount: "$150", due: "June 15, 2024" },
    { id: 4, company: "Gamma Ltd", status: "Completed", amount: "$150", due: "June 15, 2024" },
  ];

  const StatusPill: React.FC<{ status: string }> = ({ status }) => {
    const map: Record<string, string> = {
      Overdue: "bg-red-100 text-red-600",
      Completed: "bg-green-100 text-green-600",
      Pending: "bg-yellow-100 text-yellow-600",
    };
    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium ${map[status]}`}
      >
        {status}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 md:p-6 p-4">
      <h3 className="text-lg font-semibold text-primary-blue mb-6">
        Outstanding Balances
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full md:text-sm text-xs text-left">
          <thead>
            <tr className="text-gray-500 font-semibold">
              <th className="px-4 py-2 text-nowrap">Company Name</th>
              <th className="px-4 py-2 text-nowrap">Status</th>
              <th className="px-4 py-2 text-nowrap">Amount</th>
              <th className="px-4 py-2 text-nowrap">Due Date</th>
              <th className="px-4 py-2 text-nowrap">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-nowrap text-gray-800 font-medium">
                  {row.company}
                </td>
                <td className="px-4 py-3 text-nowrap">
                  <StatusPill status={row.status} />
                </td>
                <td className="px-4 py-3 text-nowrap text-gray-700">{row.amount}</td>
                <td className="px-4 py-3 text-nowrap text-gray-700">{row.due}</td>
                <td className="px-4 py-3 text-nowrap text-primary-purple font-medium space-x-2">
                  <button className="hover:underline">Send Reminder</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OutstandingBalances;
