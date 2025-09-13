# referr/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import BusinessInfo
from rest_framework import status
from .models import Referral, ReferralAssignment
from accounts.models import User, BusinessInfo, FavoriteCompany
from utils.email_service import send_app_download_email
from utils.twilio_service import TwilioService




class ListCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all companies with favorite status for current user"""
        companies = User.objects.filter(role='company').select_related('business_info')
        
        # Get user's favorite company IDs
        favorite_company_ids = set(
            FavoriteCompany.objects.filter(user=request.user).values_list('company_id', flat=True)
        )
        
        companies_list = []
        for company in companies:
            company_data = {
                "id": company.id,
                "email": company.email,
                "full_name": company.full_name,
                "phone": company.phone,
                "image": company.image.url if company.image else None,
                "is_favorite": company.id in favorite_company_ids
            }
            if hasattr(company, 'business_info'):
                business_info = company.business_info
                company_data.update({
                    "company_name": business_info.company_name,
                    "industry": business_info.industry,
                    "employees": business_info.employees,
                    "business_type": business_info.biz_type,
                    "address1": business_info.address1,
                    "address2": business_info.address2,
                    "city": business_info.city,
                    "post_code": business_info.post_code,
                    "website": business_info.website,
                    "us_state": business_info.us_state,
                })
            
            companies_list.append(company_data)

        
        return Response({
            "message": "Companies retrieved successfully",
            "companies": companies_list,
            "total": len(companies_list)
        }, status=status.HTTP_200_OK)



 

class SendReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        print(data)
        company_id = data.get("company_id")
        referred_to_email = data.get("referred_to_email")
        referred_to_phone = data.get("referred_to_phone")
        referred_to_name = data.get("referred_to_name")
        reason = data.get("reason")
        privacy = data.get("privacy", False)
        urgency_level = data.get("urgency_level")
        request_description = data.get("request_description")
        permission_consent = data.get("permission_consent", False)

        if not company_id or not referred_to_email or not referred_to_name:
            return Response(
                {"error": "company_id, email, and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # company = BusinessInfo.objects.get(id=company_id)
            COMPANY = User.objects.get(id=company_id)
        except BusinessInfo.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

        # If referred_to user exists, use it. Otherwise, create a placeholder.
        referred_to_user, _ = User.objects.get_or_create(
            email=referred_to_email,
            defaults={"full_name": referred_to_name, "phone": referred_to_phone, "role": "solo"},
        )

        referral = Referral.objects.create(
            referred_by=request.user,
            referred_to=referred_to_user,
            company=COMPANY,
            service_type=reason,
            urgency=urgency_level,
            notes=request_description,
            privacy_opted=privacy,
            permission_consent=permission_consent,
        )

        return Response(
            {
                "message": "Referral sent successfully",
                "referral_details": {
                    "reference_id": referral.reference_id,
                    "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                },
            },
            status=status.HTTP_201_CREATED,
        )
    

 
class AssignRepView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        referral_id = data.get("referral_id")
        employee_id = data.get("employee_id")
        note = data.get("notes", "")
        referral_status = data.get("status", "in_progress")  # default to in_progress
        print(data)

        # Validate referral
        try:
            referral_obj = Referral.objects.get(id=referral_id)
        except Referral.DoesNotExist:
            return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)

        # Validate employee
        employee = None
        if employee_id is not None:
            try:
                employee = User.objects.get(id=employee_id)
            except User.DoesNotExist:
                return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if assignment already exists for this referral
        assignment = ReferralAssignment.objects.filter(referral=referral_obj).last()

        if assignment:
            # Update existing assignment
            assignment.assigned_to = employee
            assignment.notes = note or assignment.notes
            assignment.status = "in_progress"
            assignment.save()
            message = "Referral assignment updated successfully"
        else:
            # Create new assignment
            assignment = ReferralAssignment.objects.create(
                referral=referral_obj,
                assigned_to=employee,
                notes=note,
            )
            message = "Referral assigned successfully"

        # Update referral status
        referral_obj.status = "cancelled" if referral_status == "reject" else "in_progress"
        referral_obj.company_approval = True if referral_status == "accept" else False
        referral_obj.save()

        return Response(
            {
                "message": message,
                "assignment_id": assignment.id,
                "referral_status": referral_obj.status,
                "assigned_to": assignment.assigned_to.full_name if assignment.assigned_to else None,
            },
            status=status.HTTP_200_OK if message.endswith("updated successfully") else status.HTTP_201_CREATED,
        )




 
class ListSoloReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        referrals = None
        if request.data.get("referral_type") == "referred_by":
            referrals = Referral.objects.filter(referred_by=request.user.id).select_related(
                'referred_to', 'company', 'company__business_info'
            )
        elif request.data.get("referral_type") == "referred_to":
            referrals = Referral.objects.filter(referred_to=request.user.id).select_related(
                'referred_to', 'company', 'company__business_info'
            )
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = referral.company.image.url
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            display_name = company_name
            if not display_name:
                display_name = business_info.user.full_name 
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_by_email": referral.referred_by.email,
                "referred_by_name": referral.referred_by.full_name,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
                "referred_by_approval": referral.referred_by_approval,
                "referral_type": request.data.get("referral_type"),
            })

        print(referral_list)

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )
    




class UpdateReferralPrivacyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        referral_id = request.data.get("referral_id")
        privacy_status = request.data.get("privacy")
        
        # Validate required fields
        if referral_id is None:
            print("Referral ID is missing")
            return Response(
                {"error": "referral_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if privacy_status is None:
            print("Privacy status is missing")
            return Response(
                {"error": "privacy status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate privacy status is boolean
        if not isinstance(privacy_status, bool):
            return Response(
                {"error": "privacy must be a boolean value (true/false)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the referral and ensure it belongs to the authenticated user
            referral = Referral.objects.get(id=referral_id, referred_by=request.user)
        except Referral.DoesNotExist:
            return Response(
                {"error": "Referral not found or you don't have permission to update it"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update the privacy status
        referral.privacy_opted = privacy_status
        referral.save()

        return Response(
            {
                "message": "Privacy status updated successfully",
            },
            status=status.HTTP_200_OK,
        )




class ListReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'solo':
            referrals = Referral.objects.all().exclude(company_id=request.user.id)
        else:
            referrals = Referral.objects.all()
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = referral.company.image.url
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            display_name = company_name
            if not display_name:
                display_name = business_info.user.full_name 
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )
    



class ListCompanyReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        if request.data.get("referral_id"):
            referrals = Referral.objects.filter(reference_id=request.data.get("referral_id"), company=request.user)
        else:
            referrals = Referral.objects.filter(company=request.user)

        referral_list = []  # Initialize referral_list
        
        for referral in referrals:
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            business_info = None  # Initialize business_info

            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    company_name = referral.company.company_name
                    company_type = getattr(referral.company, 'biz_type', "")
                if getattr(referral.company, 'image', None):
                    company_image = referral.company.image.url
            except AttributeError:
                company_name = "Unknown Company"
                company_type = "Unknown"

            # Fix the display_name logic
            display_name = company_name
            if not display_name and business_info:
                display_name = getattr(business_info.user, 'full_name', "Unknown")
            elif not display_name:
                display_name = "Unknown"

            # Build assigned employee details with error handling
            try:
                assignment = ReferralAssignment.objects.get(referral=referral)
                assigned_to_id = assignment.id
                assigned_to_name = assignment.assigned_to.full_name if assignment.assigned_to else None
                assigned_at = assignment.assigned_at.strftime("%d %b %Y") if assignment.assigned_at else None
                assigned_notes = assignment.notes if assignment.notes else None
            except ReferralAssignment.DoesNotExist:
                assigned_to_id = None
                assigned_to_name = None
                assigned_at = None
                assigned_notes = None

            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_to_phone": referral.referred_to.phone,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "company_approval": referral.company_approval,
                "referred_by_approval": referral.referred_by_approval,
                "referral_progress_status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
                "assigned_to_id": assigned_to_id,  
                "assigned_to_name": assigned_to_name,  
                "assigned_at": assigned_at,
                "assigned_notes": assigned_notes,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )



class ListAssignedReferralView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        referrals = ReferralAssignment.objects.filter(user=request.user)
        referral_list = []
        for referral in referrals:  
            # Get company information
            
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_name": referral.referred_to.full_name,
                "referred_by_name": referral.referred_to.full_name,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "status": referral.status,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )




 
class ListRepReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        referral = ReferralAssignment.objects.get(assigned_to_id=request.user.id)
        referrals = Referral.objects.filter(id=referral.referral_id).select_related(
            'referred_to', 'company', 'company__business_info'
        )
        referral_list = []
        for referral in referrals:  
            # Get company information
            company_name = ""
            company_type = ""
            company_image = None
            industry = ""
            
            try:
                if hasattr(referral.company, 'business_info'):
                    business_info = referral.company.business_info
                    company_name = business_info.company_name
                    company_type = business_info.biz_type
                    industry = business_info.industry
                elif hasattr(referral.company, 'company_name'):
                    # If company is directly a BusinessInfo object
                    company_name = referral.company.company_name
                    company_type = referral.company.biz_type if hasattr(referral.company, 'biz_type') else ""
                
                # Get company image from user profile
                if referral.company.image:
                    company_image = referral.company.image.url
            except AttributeError:
                # Handle cases where company relationships might not exist
                company_name = "Unknown Company"
                company_type = "Unknown"
            display_name = company_name
            if not display_name:
                display_name = business_info.user.full_name 
            
            referral_list.append({
                "id": referral.id,
                "reference_id": referral.reference_id,
                "referred_to_id": referral.referred_to.id,
                "referred_to_email": referral.referred_to.email,
                "referred_to_name": referral.referred_to.full_name,
                "referred_by_id": referral.referred_by.id,
                "referred_by_email": referral.referred_by.email,
                "referred_by_name": referral.referred_by.full_name,
                "industry": industry,
                "company_name": display_name,
                "company_type": company_type,
                "status": referral.status,
                "date": referral.created_at.strftime("%d %b %Y") if referral.created_at else None,
                "company_image": company_image,
                "reason": referral.service_type,
                "urgency": referral.urgency,
                "notes": referral.notes,
                "privacy": referral.privacy_opted,
            })

        return Response(
            {
                "message": "Referral list retrieved successfully",
                "referrals": referral_list,
            },
            status=status.HTTP_200_OK,
        )
    




class SendAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        referral_id = request.data.get("referral_id")
        approval = request.data.get("approval")
        if not referral_id:
            return Response(
                {"error": "referral_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            referral = Referral.objects.get(id=referral_id)
        except Referral.DoesNotExist:
            return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if approval not in [True, False]:
            return Response(
                {"error": "approval must be true or false"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        referral.referred_by_approval = approval
        referral.status = "Friend opted in" if approval else "cancelled"
        referral.save()



        return Response({"message": "Referral Accepted"}, status=status.HTTP_200_OK)



class CompleteReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        referral_id = request.data.get("referral_id")
        status_value = request.data.get("status", "completed")
        if not referral_id:
            return Response(
                {"error": "referral_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            referral = Referral.objects.get(id=referral_id)
        except Referral.DoesNotExist:
            return Response({"error": "Referral not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check assignment exists
        assignment = referral.assignments.last()
        if not assignment:
            return Response({"error": "Referral not assigned"}, status=status.HTTP_400_BAD_REQUEST)

        # Check that the logged-in user is the assigned employee
        if assignment.assigned_to != request.user:
            return Response({"error": "You are not assigned to this referral"}, status=status.HTTP_403_FORBIDDEN)

        # Update both referral and assignment statuses
        referral.status = status_value
        referral.save()
        assignment.status = status_value
        assignment.save()

        return Response({"message": "Referral marked as completed"}, status=status.HTTP_200_OK)





class SendAppInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        print(data)
        
        # Get data from request
        email = data.get("email")
        phone = data.get("phone")
        name = data.get("name")
        
        # Validate required fields
        if not email or not name:
            return Response(
                {"error": "Email and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Invalid email format"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Get sender's name from the authenticated user
            sender_name = request.user.full_name or request.user.email
            
            # Send the app download invitation email
            send_app_download_email(
                email=email,
                name=name,
                sender_name=sender_name
            )

            if phone:
                sms_result = TwilioService.send_app_download_sms(
                    phone_number=phone,
                    name=name,
                    sender_name=sender_name
                )
            
            return Response(
                {
                    "message": "Invitation sent successfully",
                },
                status=status.HTTP_200_OK,
            )
            

            
        except Exception as e:
            return Response(
                {"error": f"Failed to send invitation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        









