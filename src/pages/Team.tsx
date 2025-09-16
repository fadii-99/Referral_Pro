import React, { useEffect, useState } from "react";
import { FiFilter } from "react-icons/fi";
import Button from "./../components/Button";
import TeamRow from "../components/TeamRow";
import type { TeamMember } from "../components/TeamRow";
import Pagination from "../components/Pagination";
import EditTeamMemberModal from "../components/modals/EditTeamMemberModal";
import DeleteMemberModal from "../components/modals/DeleteMemberModal";
import AddTeamMemberModal from "../components/modals/AddTeamMemberModal";
import { useTeamMembersContext } from "../context/TeamMembersProvider";
import SmallLoader from "../components/SmallLoader";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const Team: React.FC = () => {
  const { membersFromApi, loading, loadTeam } = useTeamMembersContext();
  const [page, setPage] = useState(1);
  const [openAdd, setOpenAdd] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [selected, setSelected] = useState<TeamMember | null>(null);
  const [openDelete, setOpenDelete] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TeamMember | null>(null);

  useEffect(() => {
    void loadTeam();
  }, [loadTeam]);

  const rowsPerPage = 8;
  const start = (page - 1) * rowsPerPage;
  const current: TeamMember[] = membersFromApi.slice(start, start + rowsPerPage);
  const totalPages = Math.max(1, Math.ceil(membersFromApi.length / rowsPerPage));

  return (
    <div className="sm:p-6 p-4 flex flex-col min-h-screen">
      {/* Top bar */}
      <div className="flex sm:flex-row flex-col sm:items-center items-start sm:justify-between  sm:pb-4 pb-6">
        <h2 className="md:text-2xl text-xl font-semibold text-primary-blue">
          Team Management
        </h2>
        <div className="flex flex-row items-center gap-3 sm:mt-0 mt-4">
          <Button
            text="Add Member"
            py="py-2 sm:py-3"
            mt="mt-0"
            fullWidth={false}
            onClick={() => setOpenAdd(true)}
          />
          <button className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center">
            <FiFilter className="text-primary-purple text-lg" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 flex flex-col space-y-4">
        {/* Header */}
        <div className="overflow-x-auto">
          <div className="grid grid-cols-[0.6fr_2fr_1.8fr_1.2fr_1.2fr_1fr] min-w-[650px] px-6 py-3 text-xs sm:text-sm font-semibold text-gray-600 bg-gray-50 rounded-xl">
            <div>ID</div>
            <div>Name</div>
            <div>Email</div>
            <div>Role</div>
            <div>Status</div>
            <div className="text-right pr-3">Actions</div>
          </div>
        </div>

        {/* Rows */}
        <div className="overflow-x-auto space-y-2">
          {loading ? (
            <div className="py-6 flex justify-center">
              <SmallLoader />
            </div>
          ) : current.length === 0 ? (
            <div className="text-sm p-8 text-center text-gray-500">
              No team members found.
            </div>
          ) : (
            current.map((m) => (
              <TeamRow
                key={m.id}
                member={m}
                onEdit={(mem) => {
                  setSelected(mem);
                  setOpenEdit(true);
                }}
                onDelete={(mem) => {
                  setDeleteTarget(mem);
                  setOpenDelete(true);
                }}
              />
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

      {/* Modals */}
      <EditTeamMemberModal
        open={openEdit}
        member={selected}
        onClose={() => setOpenEdit(false)}
        onSave={async () => {
          await loadTeam();
        }}
      />
      <DeleteMemberModal
        open={openDelete}
        member={deleteTarget}
        onClose={() => setOpenDelete(false)}
      />
      <AddTeamMemberModal open={openAdd} onClose={() => setOpenAdd(false)} />

      {/* Toasts */}
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />
    </div>
  );
};

export default Team;
