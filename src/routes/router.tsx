import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import Loader from "../components/Loader.tsx";
import PrivateRoute from "./../components/PrivateRoute.tsx"

// Auth
const Login = lazy(() => import("./../pages/Login"));
const Forget = lazy(() => import("./../pages/Forget"));
const CreatePassword = lazy(() => import("./../pages/CreatePassword"));
const PasswordVerification = lazy(() => import("./../pages/PasswordVerification"));
const PasswordSuccess = lazy(() => import("./../pages/PasswordSuccess"));
const Welcome = lazy(() => import("./../pages/Welcome"));
const BusinessRegistration = lazy(() => import("./../pages/BusinessRegistration"));
const BusinessType = lazy(() => import("./../pages/BusinessType"));
const CompanyInformation = lazy(() => import("./../pages/CompanyInformation"));
const SubscriptionPlan = lazy(() => import("./../pages/SubscriptionPlan"));
const PaymentMethod = lazy(() => import("./../pages/PaymentMethod"));
const PasswordCreation = lazy(() => import("./../pages/PasswordCreation"));


// Dashboard
import DashboardParent from "./DashboardParent";
const Dashboard = lazy(() => import("./../pages/Dashboard"));
const Analytics = lazy(() => import("./../pages/Analytics"));
const Team = lazy(() => import("./../pages/Team"));
const Referral = lazy(() => import("./../pages/Referral"));
const ReferralDetail = lazy(() => import("./../pages/ReferralDetail"));
const Notifications = lazy(() => import("./../pages/Notifications.tsx"));
const Profile = lazy(() => import("./../pages/Profile.tsx"));


// Admin
// import AdminParent from "./AdminParent.tsx";
// const AdminDashboard= lazy(() => import("./../adminPages/AdminDashboard.tsx"));
// const AdminFinancial = lazy(() => import("./../adminPages/AdminFinancial.tsx"));
// const AdminUsers = lazy(() => import("./../adminPages/AdminUsers.tsx")); // 👈 NEW
// const AdminCompany = lazy(() => import("./../adminPages/AdminCompany.tsx")); // 👈 NEW
// const AdminTickets = lazy(() => import("./../adminPages/AdminTickets.tsx")); // 👈 NEW




const router = createBrowserRouter([
  // Public Routes
  {
    path: "/",
    element: (
      <Suspense fallback={<Loader />}>
        <Welcome />
      </Suspense>
    ),
  },
  {
    path: "/Login",
    element: (
      <Suspense fallback={<Loader />}>
        <Login />
      </Suspense>
    ),
  },
  {
    path: "/ForgetPassword",
    element: (
      <Suspense fallback={<Loader />}>
        <Forget />
      </Suspense>
    ),
  },
  {
    path: "/CreatePassword",
    element: (
      <Suspense fallback={<Loader />}>
        <CreatePassword />
      </Suspense>
    ),
  },
  {
    path: "/PasswordVerification",
    element: (
      <Suspense fallback={<Loader />}>
        <PasswordVerification />
      </Suspense>
    ),
  },
  {
    path: "/PasswordSuccess",
    element: (
      <Suspense fallback={<Loader />}>
        <PasswordSuccess />
      </Suspense>
    ),
  },
  {
    path: "/BusinessRegistration",
    element: (
      <Suspense fallback={<Loader />}>
        <BusinessRegistration />
      </Suspense>
    ),
  },
  {
    path: "/BusinessType",
    element: (
      <Suspense fallback={<Loader />}>
        <BusinessType />
      </Suspense>
    ),
  },
  {
    path: "/CompanyInformation",
    element: (
      <Suspense fallback={<Loader />}>
        <CompanyInformation />
      </Suspense>
    ),
  },
  {
    path: "/SubscriptionPlan",
    element: (
      <Suspense fallback={<Loader />}>
        <SubscriptionPlan />
      </Suspense>
    ),
  },
  {
    path: "/PaymentMethod",
    element: (
      <Suspense fallback={<Loader />}>
        <PaymentMethod />
      </Suspense>
    ),
  },
  {
    path: "/PasswordCreation",
    element: (
      <Suspense fallback={<Loader />}>
        <PasswordCreation />
      </Suspense>
    ),
  },

  // 🔒 Private Dashboard Routes
  {
    path: "/Dashboard",
    element: (
      <Suspense fallback={<Loader />}>
        <PrivateRoute />
      </Suspense>
    ),
    children: [
      {
        element: (
          <Suspense fallback={<Loader />}>
            <DashboardParent />
          </Suspense>
        ),
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<Loader />}>
                <Dashboard />
              </Suspense>
            ),
          },
          {
            path: "Analytics",
            element: (
              <Suspense fallback={<Loader />}>
                <Analytics />
              </Suspense>
            ),
          },
          {
            path: "Team",
            element: (
              <Suspense fallback={<Loader />}>
                <Team />
              </Suspense>
            ),
          },
          {
            path: "Referral",
            element: (
              <Suspense fallback={<Loader />}>
                <Referral />
              </Suspense>
            ),
          },
          {
            path: "Referral/:id",
            element: (
              <Suspense fallback={<Loader />}>
                <ReferralDetail />
              </Suspense>
            ),
          },
          {
            path: "Notifications",
            element: (
              <Suspense fallback={<Loader />}>
                <Notifications />
              </Suspense>
            ),
          },
          {
            path: "Profile",
            element: (
              <Suspense fallback={<Loader />}>
                <Profile />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },

  // 🔒 Admin Dashboard Routes
// {
//   path: "/Admin",
//   element: (
//     <Suspense fallback={<Loader />}>
//       <AdminParent />
//     </Suspense>
//   ),
//   children: [
//     {
//       index: true,
//       element: (
//         <Suspense fallback={<Loader />}>
//           <AdminDashboard />
//         </Suspense>
//       ),
//     }
//     ,
//       {
//       path: "Financial",
//       element: (
//         <Suspense fallback={<Loader />}>
//           <AdminFinancial />
//         </Suspense>
//       ),
//     }
//     ,
//     {
//       path: "Users",
//       element: (
//         <Suspense fallback={<Loader />}>
//           <AdminUsers />
//         </Suspense>
//       ),
//     }
//     ,
//       {
//         path: "Company",
//         element: (
//           <Suspense fallback={<Loader />}>
//             <AdminCompany />
//           </Suspense>
//         ),
//       },
//       {
//         path: "Tickets",
//         element: (
//           <Suspense fallback={<Loader />}>
//             <AdminTickets />
//           </Suspense>
//         ),
//       },
//   ],
// },
]);

export default router;
