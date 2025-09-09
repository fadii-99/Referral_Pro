import React, { useState } from "react";
import Button from "../components/Button";
import EditProfileModal from "../components/modals/EditProfileModal";
import { FiMail, FiPhone } from "react-icons/fi";

export type ProfileData = {
  name: string;
  email: string;
  phone: string;
  avatar: string;
};

const Profile: React.FC = () => {
  // dummy initial data
  const [me, setMe] = useState<ProfileData>({
    name: "John Smith",
    email: "jaywilliams@gmail.com",
    phone: "000 1234567",
    avatar: "https://i.pravatar.cc/160?img=12",
  });

  const [open, setOpen] = useState(false);

  return (
    <div className="p-10">

      {/* Card */}
      <div className="bg-white rounded-2xl border border-black/5 shadow-sm p-10 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* Left: Image */}
          <div className="flex items-center md:justify-start justify-center border-r col-span-1 pr-4">
            <img
              src={me.avatar}
              alt={me.name}
              className="h-full w-full rounded-full object-cover ring-2 ring-white shadow"
            />
          </div>

          {/* Right: Info */}
          <div className="col-span-2">
            <div className="text-3xl font-semibold text-primary-blue">{me.name}</div>

            <div className="mt-3 flex flex-wrap items-center gap-5 text-[13px] text-gray-500">
              <span className="inline-flex items-center gap-2">
                <FiMail className="text-primary-purple" />
                {me.email}
              </span>
              <span className="inline-flex items-center gap-2">
                <FiPhone className="text-primary-purple" />
                {me.phone}
              </span>
            </div>

            <div className="mt-10">
              <Button
                text="Edit Profile"
                fullWidth={false}
                mt="mt-0"
                py="py-2 sm:py-3"
                onClick={() => setOpen(true)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      <EditProfileModal
        open={open}
        profile={me}
        onClose={() => setOpen(false)}
        onSave={(updated) => {
          setMe(updated);
          setOpen(false);
        }}
      />
    </div>
  );
};

export default Profile;
