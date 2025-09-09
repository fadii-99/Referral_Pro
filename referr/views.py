# referr/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import BusinessInfo
from rest_framework import status
from .models import Referral
from accounts.models import User, BusinessInfo



class CompaniesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = BusinessInfo.objects.select_related('user').all()
        companies_list = []
        
        for company in companies:
            # Get company image from the associated user
            company_image = None
            if company.user.image:
                company_image = company.user.image.url
            
            # If company_name is None or empty, use full_name from user table
            display_name = company.company_name
            if not display_name:
                display_name = company.user.full_name or "Unknown Company"
            
            companies_list.append({
                "id": company.id,
                "company_name": display_name,
                "image": company_image,
                "business_type": company.biz_type,
                "industry": company.industry,
                "rating": 4.2, 
                "city": company.city,
                "category": company.industry
            })

        
        return Response({"companies": companies_list}, status=status.HTTP_200_OK)



 

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
            company = BusinessInfo.objects.get(id=company_id)
            COMPANY = User.objects.get(id=company.user.id)
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
    


class ListReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        referrals = Referral.objects.filter(referred_by=request.user).select_related(
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
        referrals = Referral.objects.filter(company=request.user)
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



