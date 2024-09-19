from django.urls import path

from .views import (RegistrationAPIView, LoginAPIView,BlogListCreateAPIView, BlogDetailAPIView,
    CommentListCreateAPIView, CommentDetailAPIView,ShareBlogAPIView)



urlpatterns = [
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('blogs/', BlogListCreateAPIView.as_view(), name='blog-list-create'),
    path('blogs/<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
    path('comments/', CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailAPIView.as_view(), name='comment-detail'),
    path('blogs/share/<int:blog_id>/', ShareBlogAPIView.as_view(), name='blog-share'),
]
