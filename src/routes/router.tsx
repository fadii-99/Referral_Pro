import  { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';



const Login = lazy(() => import('./../pages/Login'));
const Forget = lazy(() => import('./../pages/Forget'));
const CreatePassword = lazy(() => import('./../pages/CreatePassword'));
const PasswordVerification = lazy(() => import('./../pages/PasswordVerification'));
const PasswordSuccess = lazy(() => import('./../pages/PasswordSuccess'));
const Welcome = lazy(() => import('./../pages/Welcome'));

const BusinessRegistration = lazy(() => import('./../pages/BusinessRegistration'));
const BusinessType = lazy(() => import('./../pages/BusinessType'));
const CompanyInformation=lazy(() => import('./../pages/CompanyInformation'));
const SubscriptionPlan=lazy(() => import('./../pages/SubscriptionPlan'));
const PaymentMethod=lazy(() => import('./../pages/PaymentMethod'));
const PasswordCreation=lazy(() => import('./../pages/PasswordCreation'));
const Dashboard=lazy(() => import('./../pages/Dashboard'));


const router = createBrowserRouter([
    {
    path: '/',
    element: (
      <Suspense fallback={''}>
        <Welcome/>
      </Suspense>
    )
  },
  {
    path: '/Login',
    element: (
      <Suspense fallback={''}>
        <Login/>
      </Suspense>
    )
  },
    {
    path: '/ForgetPassword',
    element: (
      <Suspense fallback={''}>
        <Forget/>
      </Suspense>
    )
  }
  ,
    {
    path: '/CreatePassword',
    element: (
      <Suspense fallback={''}>
        <CreatePassword/>
      </Suspense>
    )
  }
    ,
    {
    path: '/PasswordVerification',
    element: (
      <Suspense fallback={''}>
        <PasswordVerification/>
      </Suspense>
    )
  }
   ,
    {
    path: '/PasswordSuccess',
    element: (
      <Suspense fallback={''}>
        <PasswordSuccess/>
      </Suspense>
    )
  }
  ,
    {
    path: '/BusinessRegistration',
    element: (
      <Suspense fallback={''}>
        <BusinessRegistration/>
      </Suspense>
    )
  }
    ,
    {
    path: '/BusinessType',
    element: (
      <Suspense fallback={''}>
        <BusinessType/>
      </Suspense>
    )
  }
     ,
    {
    path: '/CompanyInformation',
    element: (
      <Suspense fallback={''}>
        <CompanyInformation/>
      </Suspense>
    )
  }
    ,
    {
    path: '/SubscriptionPlan',
    element: (
      <Suspense fallback={''}>
        <SubscriptionPlan/>
      </Suspense>
    )
  }
   ,
    {
    path: '/PaymentMethod',
    element: (
      <Suspense fallback={''}>
        <PaymentMethod/>
      </Suspense>
    )
  }
   ,
    {
    path: '/PasswordCreation',
    element: (
      <Suspense fallback={''}>
        <PasswordCreation/>
      </Suspense>
    )
    }
     ,
    {
    path: '/Dashboard',
    element: (
      <Suspense fallback={''}>
        <Dashboard/>
      </Suspense>
    )
    }
]);


export default router;
