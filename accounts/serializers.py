# accounts/serializers.py
from rest_framework import serializers
from .models import User, Review, ReviewImage


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "image", "role", "password"]
        read_only_fields = ["id", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class ReviewImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'image_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def get_image_url(self, obj):
        """Get the full S3 URL for the image"""
        return obj.get_image_url()


class ReviewSerializer(serializers.ModelSerializer):
    review_gallery = ReviewImageSerializer(many=True, read_only=True)
    review_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=3,  # Maximum 3 images
        help_text="Upload up to 3 review images"
    )
    time_ago = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'review_rating', 'review_feedback', 'review_by_name', 
            'review_by_image', 'time_ago', 'business', 'business_name',
            'review_gallery', 'review_images', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'review_by_name', 'review_by_image', 'time_ago', 
            'created_at', 'updated_at', 'business_name'
        ]

    def get_time_ago(self, obj):
        """Get human-readable time since review creation"""
        return obj.time_ago()
    
    def get_business_name(self, obj):
        """Get the business/company name"""
        if hasattr(obj.business, 'business_info'):
            return obj.business.business_info.company_name
        return obj.business.full_name or obj.business.email

    def create(self, validated_data):
        # Extract images from validated_data
        images_data = validated_data.pop('review_images', [])
        
        # Set the reviewer
        validated_data['review_by'] = self.context['request'].user
        
        # Create the review
        review = Review.objects.create(**validated_data)
        
        # Create review images
        for image_data in images_data:
            ReviewImage.objects.create(review=review, image=image_data)
        
        return review

    def update(self, instance, validated_data):
        # Extract images from validated_data
        images_data = validated_data.pop('review_images', [])
        
        # Update review fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If new images are provided, replace existing ones
        if images_data:
            # Delete existing images
            instance.review_gallery.all().delete()
            
            # Create new images
            for image_data in images_data:
                ReviewImage.objects.create(review=instance, image=image_data)
        
        return instance

    def validate(self, data):
        """Custom validation"""
        request = self.context.get('request')
        
        # Ensure only solo users can create reviews
        if request and request.user.role != 'solo':
            raise serializers.ValidationError("Only solo users can create reviews.")
        
        # Ensure business is actually a company
        business = data.get('business')
        if business and business.role != 'company':
            raise serializers.ValidationError("Reviews can only be given to businesses/companies.")
        
        # For creation, check if user already reviewed this business
        if not self.instance and request:
            if Review.objects.filter(review_by=request.user, business=business).exists():
                raise serializers.ValidationError("You have already reviewed this business.")
        
        return data


class BusinessReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews received by a business"""
    review_gallery = ReviewImageSerializer(many=True, read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'review_rating', 'review_feedback', 'review_by_name', 
            'review_by_image', 'time_ago', 'review_gallery', 'created_at'
        ]
        read_only_fields = '__all__'

    def get_time_ago(self, obj):
        """Get human-readable time since review creation"""
        return obj.time_ago()
