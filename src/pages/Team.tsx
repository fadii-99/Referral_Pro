import React, { useState } from "react";
import { FiFilter, FiSliders } from "react-icons/fi";
import Button from "./../components/Button";
import TeamRow from "../components/TeamRow";
import type { TeamMember } from "../components/TeamRow";
import Pagination from "../components/Pagination";
import EditTeamMemberModal from "../components/modals/EditTeamMemberModal";
import DeleteMemberModal from "../components/modals/DeleteMemberModal";
import AddTeamMemberModal from "../components/modals/AddTeamMemberModal";
import { useTeamMembersContext } from "../context/TeamMembersProvider";


const Team: React.FC = () => {
  const { membersFromApi, loading, error, loadTeam } = useTeamMembersContext();
  const [page, setPage] = useState(1);
  const [openAdd, setOpenAdd] = useState(false);

  // edit modal state
  const [openEdit, setOpenEdit] = useState(false);
  const [selected, setSelected] = useState<TeamMember | null>(null);

  // delete modal state
  const [openDelete, setOpenDelete] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TeamMember | null>(null);

  // useEffect(() => {
  //   console.log("[Team page] membersFromApi:", membersFromApi);
  // }, [membersFromApi]);

  const rowsPerPage = 8;
  const start = (page - 1) * rowsPerPage;
  const current: TeamMember[] = membersFromApi.slice(start, start + rowsPerPage);
  const totalPages = Math.max(1, Math.ceil(membersFromApi.length / rowsPerPage));

  return (
    <div className="p-6 flex flex-col min-h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between pb-4">
        <h2 className="text-2xl font-semibold text-primary-blue">Team Management</h2>
        <div className="flex flex-row items-center gap-3">
          <Button text="Add Member" py="py-2 sm:py-3" mt="mt-0" fullWidth={false} onClick={() => setOpenAdd(true)} />
          <button className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center">
            <FiFilter className="text-primary-purple text-lg" />
          </button>
          <button className="h-10 w-10 rounded-xl bg-white border border-black/5 shadow-sm flex items-center justify-center">
            <FiSliders className="text-primary-purple text-lg" />
          </button>
        </div>
      </div>

      {/* Loading / Error */}
      {loading && <p className="text-sm text-gray-600">Loading team...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Table container */}
      <div className="flex-1 flex flex-col space-y-4">
        {/* Header */}
        <div className="grid grid-cols-[0.6fr_2fr_1.8fr_1.2fr_1.2fr_1fr] px-6 py-3 text-xs sm:text-sm font-semibold text-gray-600 bg-gray-50 rounded-xl">
          <div>ID</div>
          <div>Name</div>
          <div>Email</div>
          <div>Role</div>
          <div>Status</div>
          <div className="text-right pr-3">Actions</div>
        </div>

        {/* Rows */}
        <div className="space-y-2">
          {current.length === 0 && !loading ? (
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
                  setDeleteTarget(mem);   // 👈 jis member pe delete click hoga usko set karo
                  setOpenDelete(true);    // 👈 modal open hoga
                }}
              />
            ))
          )}
        </div>
      </div>

      {/* Pagination at the bottom */}
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
    </div>
  );
};

export default Team;
