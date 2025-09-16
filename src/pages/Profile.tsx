import React, { useState } from "react";
import Button from "../components/Button";
import EditProfileModal from "../components/modals/EditProfileModal";
import { FiMail, FiPhone } from "react-icons/fi";
import { useUserContext } from "../context/UserProvider";
import SmallLoader from "../components/SmallLoader";

const Profile: React.FC = () => {
  const { user, loading } = useUserContext();
  const [open, setOpen] = useState(false);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <SmallLoader />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="p-10 text-center text-gray-500">Failed to load profile.</div>
    );
  }


  return (
    <div className="p-10">
      <div className="bg-white rounded-2xl border border-black/5 shadow-sm sm:p-10 p-8 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 md:gap-6 items-center">
          <div className="flex items-center md:justify-start justify-center md:border-r col-span-1 md:pr-4 md:mb-0 mb-8">
            {user.avatar && (
              <img
                src={user.avatar}
                alt={user.name}
                className="h-40 w-40 rounded-full object-cover ring-2 ring-white shadow"
              />
            )}
          </div>

          <div className="col-span-2">
            <div className="text-3xl font-semibold text-primary-blue">
              {user.name}
            </div>

            <div className="mt-3 flex flex-wrap items-center sm:gap-5 gap-3 sm:text-sm text-xs text-gray-500">
              <span className="inline-flex items-center gap-2">
                <FiMail className="text-primary-purple" />
                {user.email}
              </span>
              {user.phone && (
                <span className="inline-flex items-center gap-2">
                  <FiPhone className="text-primary-purple" />
                  {user.phone}
                </span>
              )}
            </div>

            <div className="mt-10">
              <Button
                text="Edit Profile"
                onClick={() => setOpen(true)}
                fullWidth={false}
                mt="mt-0"
                py="py-2 sm:py-3"
              />
            </div>
          </div>
        </div>
      </div>

      <EditProfileModal open={open} onClose={() => setOpen(false)} />
    </div>
  );
};

export default Profile;
