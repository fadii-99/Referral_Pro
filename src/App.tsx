import './App.css';
import { RouterProvider } from 'react-router-dom';
import router from './routes/router';
import { RegistrationProvider } from './context/RegistrationProvider';


function App() {


  return (
  <>
  <RegistrationProvider>
          <RouterProvider router={router} /> 
  </RegistrationProvider>
  </>
  )
}


export default App;
