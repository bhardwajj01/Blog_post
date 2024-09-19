from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from .models import Blog, Tag, Comment
from .serializers import (RegistrationSerializer,BlogSerializer,CommentSerializer,LoginSerializer)
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework.pagination import PageNumberPagination




class RegistrationAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'success': True,
                            'message': 'User created successfully'},
                             status=status.HTTP_201_CREATED)
        else:
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginAPIView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            if user:
                token=AccessToken.for_user(user)
                token=str(token)

                return Response({
                    'status': True,
                    'message': 'Login successfully',
                    'access_token': token,
                }, status=status.HTTP_200_OK)
            else:
                return Response({'status': False, 'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BlogListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tag_name = request.query_params.get('tag', None)
        search_term = request.query_params.get('search', None)

        if tag_name:
            blogs = Blog.objects.filter(tags__name__icontains=tag_name).distinct()
        elif search_term:
            search_query = SearchQuery(search_term)
            blogs = Blog.objects.annotate(
                rank=SearchRank(SearchVector('title', 'content'), search_query)
            ).filter(rank__gte=0.1).order_by('-rank')
        else:
            blogs = Blog.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = 5
        result_page = paginator.paginate_queryset(blogs, request)
        serializer = BlogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['author'] = request.user.id
        tags = data.pop('tags', [])
        serializer = BlogSerializer(data=data)
        if serializer.is_valid():
            blog = serializer.save()
            for tag_id in tags:
                try:
                    tag = Tag.objects.get(id=tag_id)
                    blog.tags.add(tag)
                except Tag.DoesNotExist:
                    continue
            return Response({
                'success': True,
                'message': 'Blog created successfully',
                'blog': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class BlogDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk)
            serializer = BlogSerializer(blog)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Blog.DoesNotExist:
            return Response({
                'error': 'Blog not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk)
            if blog.author != request.user:
                return Response({'error': 'You do not have permission to edit this blog'}, status=status.HTTP_403_FORBIDDEN)

            serializer = BlogSerializer(blog, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Blog updated successfully',
                    'blog': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Blog.DoesNotExist:
            return Response({
                'error': 'Blog not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk)
            if blog.author != request.user:
                return Response({'error': 'You do not have permission to delete this blog'}, status=status.HTTP_403_FORBIDDEN)

            blog.delete()
            return Response({
                'success': True,
                'message': 'Blog deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Blog.DoesNotExist:
            return Response({
                'error': 'Blog not found'
            }, status=status.HTTP_404_NOT_FOUND)



class CommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            return Response({
                'success': True,
                'message': 'Comment created successfully',
                'comment': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CommentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            serializer = CommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response({
                'error': 'Comment not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            if comment.author != request.user:
                return Response({'error': 'You do not have permission to edit this comment'}, status=status.HTTP_403_FORBIDDEN)

            serializer = CommentSerializer(comment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Comment updated successfully',
                    'comment': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Comment.DoesNotExist:
            return Response({
                'error': 'Comment not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            if comment.author != request.user:
                return Response({'error': 'You do not have permission to delete this comment'}, status=status.HTTP_403_FORBIDDEN)

            comment.delete()
            return Response({
                'success': True,
                'message': 'Comment deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Comment.DoesNotExist:
            return Response({
                'error': 'Comment not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            if not comment.likes:
                comment.likes = 1
            else:
                comment.likes += 1
            comment.save()
            serializer = CommentSerializer(comment)
            return Response({
                'success': True,
                'message': 'Comment liked successfully',
                'comment': serializer.data
            }, status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response({
                'error': 'Comment not found'
            }, status=status.HTTP_404_NOT_FOUND)





class ShareBlogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, blog_id):
        try:
            blog = Blog.objects.get(id=blog_id)
            recipient_email = request.data.get('email')
            message = f"Check out this blog post titled '{blog.title}': {blog.content}"
            
            send_mail(
                subject=f"Blog Share: {blog.title}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
            )
            return Response({'message': 'Blog shared successfully'}, status=status.HTTP_200_OK)
        except Blog.DoesNotExist:
            return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
