from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from .models import Blog, Tag, Comment



class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2')

        if password != password2:
            raise ValidationError({'password2': 'Passwords must match.'})

        if User.objects.filter(email=data['email']).exists():
            raise ValidationError({'email': 'User with this email already exists.'})
        
        if User.objects.filter(username=data['username']).exists():
            raise ValidationError({'username': 'User with this username already exists.'})

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = User.objects.filter(Q(email=username) | Q(username=username)).first()

        if user:
            if check_password(password, user.password):
                data['user'] = user
            else:
                raise serializers.ValidationError('Authentication failed. Please try again.')
        else:
            raise serializers.ValidationError('User with this email or username does not exist.')
        
        return data
    



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']



class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'blog', 'author', 'content', 'created_at', 'likes']
        read_only_fields = ['author', 'created_at', 'likes']

    def create(self, validated_data):
        request = self.context.get('request')
        author = request.user if request and hasattr(request, 'user') else None
        return Comment.objects.create(author=author, **validated_data)




class BlogSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'tags', 'comments']



