import './App.css';
import { RouterProvider } from 'react-router-dom';
import router from './routes/router';
import { RegistrationProvider } from './context/RegistrationProvider';
import { TeamMembersProvider } from './context/TeamMembersProvider';
import { ReferralProvider } from './context/ReferralProvider';


function App() {


  return (
  <>
   <ReferralProvider>
      <TeamMembersProvider>
        <RegistrationProvider>
                <RouterProvider router={router} /> 
        </RegistrationProvider>
      </TeamMembersProvider>
    </ReferralProvider>
  </>
  )
}


export default App;
