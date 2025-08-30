import referralProLogo from './../assets/referralProLogo.png';
import sideComponentImage from './../assets/sideComponentImage.png';


function SideDesign() {


    return (
          <div className="w-full h-screen bg-primary-blue md:col-span-2 p-8 relative hidden md:block">
            <div className='flex flex-col items-start gap-10'>
                <div>
                    <img src={referralProLogo} alt="referral-pro-logo" className='h-14 w-auto' />
                </div>
                <h1 className='text-4xl text-white font-bold mt-10'>Referring made simple track rewards on the go.</h1>
                <p className='text-lg text-gray-100 font-light'>Turn connections into rewards—hassle free</p>
            </div>
            {/*  */}
            <div className='absolute bottom-0 left-0'>
                <img src={sideComponentImage} alt="side-component-image" className='w-52 h-auto opacity-10' />
            </div>
          </div>
    )
}

export default SideDesign;