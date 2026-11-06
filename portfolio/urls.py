from rest_framework.routers import DefaultRouter
from django.urls import path,include
from .views import *
router=DefaultRouter()
for prefix,view,name in [('profile',ProfileViewSet,'profile'),('skills',SkillViewSet,'skill'),('experiences',ExperienceViewSet,'experience'),('education',EducationViewSet,'education'),('projects',ProjectViewSet,'project'),('categories',CategoryViewSet,'category'),('tags',TagViewSet,'tag'),('posts',PostViewSet,'post'),('comments',CommentModerationViewSet,'comment'),('contact',ContactViewSet,'contact')]: router.register(prefix,view,basename=name)
urlpatterns=[path('profile/',ProfileViewSet.as_view({'get':'list','patch':'partial_update_singleton'}),name='profile-singleton'),path('comments/replies/',CommentReplyCreateView.as_view(),name='comment-reply-create'),path('',include(router.urls)),path('dashboard/stats/',DashboardStatsView.as_view())]
