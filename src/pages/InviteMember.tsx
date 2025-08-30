import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import SideDesign from "../components/SideDesign";
import Button from "../components/Button";
import MultiStepHeader from "./../components/MultiStepHeader";

const ALL_MEMBERS = [
  "alice@example.com",
  "bob@example.com",
  "carol@example.com",
  "dave@example.com",
  "eve@example.com",
];

const InviteMember: React.FC = () => {
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<string>("");

  const [members, setMembers] = useState<string[]>([]);

  const available = useMemo(
    () => ALL_MEMBERS.filter((m) => !members.includes(m)),
    [members]
  );

  const addSelected = () => {
    if (!selected) return;
    if (members.includes(selected)) return;
    setMembers((prev) => [...prev, selected]);
    setSelected("");
    setOpen(false);
  };

  const removeMember = (email: string) =>
    setMembers((prev) => prev.filter((m) => m !== email));

  const sendInvites: React.MouseEventHandler<HTMLButtonElement> = () => {
    if (!members.length) return;

    console.log("Sending invites to:", members);
    navigate("/finish"); 
  };

  return (
    <div className="grid md:grid-cols-5 w-full min-h-screen">
      <SideDesign />
      <div className="md:col-span-3 flex flex-col bg-[#F4F2FA]">
        <div className="sticky top-10 z-30 backdrop-blur w-full max-w-lg mx-auto">
          <div className="px-4">
            <MultiStepHeader title="Invite Team Members" current={7} total={7} onBack={() => navigate(-1)} />
          </div>
        </div>

        <div className="flex-1 flex items-start md:items-center justify-center px-4 pt-10 md:pt-0">
          <div className="w-full max-w-lg">
            <div className="mb-6">
              <label className="block text-[11px] text-primary-blue font-semibold mb-1.5">
                Invitation Team
              </label>

              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 text-primary-purple/80"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  >
                    <path d="M16 11a3 3 0 100-6 3 3 0 000 6Z" />
                    <path d="M8 13a3 3 0 100-6 3 3 0 000 6Z" />
                    <path d="M2 20a6 6 0 0112 0M10 20a6 6 0 0112 0" />
                  </svg>
                </span>

                <button
                  type="button"
                  onClick={() => setOpen((s) => !s)}
                  className="w-full min-h-[52px] pl-12 pr-10 py-3 rounded-full bg-white border border-gray-200 text-left
                             text-xs md:text-sm text-gray-800 outline-none"
                >
                  {selected ? (
                    // chip style selected value
                    <span className="inline-flex items-center gap-2 rounded-full bg-primary-purple/10 text-primary-blue px-3 py-1 text-[11px]">
                      {selected}
                    </span>
                  ) : (
                    <span className="text-gray-400">Add Member</span>
                  )}
                </button>

                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>

                {open && (
                  <ul className="absolute z-20 mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-lg max-h-64 overflow-auto">
                    {available.length ? (
                      available.map((email) => (
                        <li key={email}>
                          <button
                            type="button"
                            onClick={() => {
                              setSelected(email);
                              setOpen(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm hover:bg-primary-purple/5"
                          >
                            {email}
                          </button>
                        </li>
                      ))
                    ) : (
                      <li className="px-4 py-3 text-sm text-gray-500">No more members</li>
                    )}
                  </ul>
                )}
              </div>
            </div>

            {selected && (
              <div className="mb-6">
                <Button text="Add" onClick={addSelected} />
              </div>
            )}

            {members.length > 0 && (
              <div className="mb-6">
                <div className="text-primary-blue font-semibold text-sm mb-2">Member List</div>
                <div className="divide-y divide-gray-200 rounded-2xl bg-white/60">
                  {members.map((email) => (
                    <div key={email} className="flex items-center justify-between px-3 py-3">
                      <div className="flex items-center gap-3">
                        <span className="h-8 w-8 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center text-[11px] text-gray-500">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <path d="M12 12a4 4 0 100-8 4 4 0 000 8Z" />
                            <path d="M3 20a9 9 0 0118 0" />
                          </svg>
                        </span>
                        <span className="text-sm text-primary-blue">{email}</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => removeMember(email)}
                        className="text-xs text-gray-500 hover:text-primary-purple"
                        title="Remove"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-3">
              <button
                type="button"
                onClick={sendInvites}
                disabled={members.length === 0}
                className="mt-0 w-full rounded-full py-5 text-primary-blue text-sm font-semibold
                           shadow-[0_10px_30px_rgba(0,0,0,0.12)] bg-secondary-blue transition
                           hover:shadow-[0_12px_36px_rgba(0,0,0,0.15)] hover:scale-[102%] duration-300
                           disabled:opacity-60 disabled:cursor-not-allowed"
              >
                Send Invites
              </button>
            </div>

            <p className="text-center text-xs text-primary-blue/70 cursor-pointer hover:text-primary-purple" onClick={() => navigate("/finish")}>
              Skip
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteMember;
