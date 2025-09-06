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
        companies = BusinessInfo.objects.all().values(
            "id", "company_name", "industry", "city", "website"
        )
        return Response({"companies": list(companies)}, status=status.HTTP_200_OK)



 

class SendReferralView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        company_id = data.get("company_id")
        referred_to_email = data.get("email")
        referred_to_phone = data.get("phone")
        referred_to_name = data.get("name")
        reason = data.get("reason")
        privacy = data.get("privacy", False)
        urgency_level = data.get("urgency_level")
        request_description = data.get("request_description")
        permission_concent = data.get("permission_concent", False)

        if not company_id or not referred_to_email or not referred_to_name:
            return Response(
                {"error": "company_id, email, and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            company = BusinessInfo.objects.get(id=company_id)
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
            company=company,
            service_type=reason,
            urgency=urgency_level,
            notes=request_description,
            privacy_opted=privacy,
            permission_concent=permission_concent,
        )

        return Response(
            {
                "message": "Referral sent successfully",
                "referral": {
                    "id": referral.id,
                    "referred_by": referral.referred_by.email,
                    "referred_to": referral.referred_to.email,
                    "company": referral.company.company_name,
                    "reason": referral.service_type,
                    "urgency": referral.urgency,
                    "notes": referral.notes,
                    "privacy": referral.privacy_opted,
                    "status": referral.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )





