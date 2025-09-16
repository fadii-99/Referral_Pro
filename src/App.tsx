import './App.css';
import { RouterProvider } from 'react-router-dom';
import router from './routes/router';
import { RegistrationProvider } from './context/RegistrationProvider';
import { TeamMembersProvider } from './context/TeamMembersProvider';
import { ReferralProvider } from './context/ReferralProvider';
import { UserProvider } from './context/UserProvider';



function App() {

  return (
  <>
    <UserProvider>
      <ReferralProvider>
          <TeamMembersProvider>
            <RegistrationProvider>
                    <RouterProvider router={router} /> 
            </RegistrationProvider>
          </TeamMembersProvider>
        </ReferralProvider>
    </UserProvider>
  </>
  )
}


export default App;
