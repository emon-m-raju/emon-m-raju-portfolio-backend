from django.db.models import F,Count,Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate,update_session_auth_hash
from rest_framework import viewsets,status,filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from .serializers import *
from .permissions import ContactMessagePermission, ContactSubmissionPermission, IsOwnerOrReadOnly
from .throttles import CommentThrottle,ContactThrottle,LikeThrottle
class OwnerOnly(IsAuthenticated):
 def has_permission(self,request,view): return super().has_permission(request,view) and request.user.is_superuser
class LoginView(APIView):
 permission_classes=[AllowAny]
 def post(self,request):
  user=authenticate(username=request.data.get('username'),password=request.data.get('password'))
  if not user or not user.is_superuser: return Response({'detail':'Invalid credentials.'},status=401)
  refresh=RefreshToken.for_user(user); return Response({'access':str(refresh.access_token),'refresh':str(refresh),'user':{'id':user.id,'username':user.username,'email':user.email}})
class MeView(APIView):
 permission_classes=[OwnerOnly]
 def get(self,request): return Response({'id':request.user.id,'username':request.user.username,'email':request.user.email})
class LogoutView(APIView):
 permission_classes=[OwnerOnly]
 def post(self,request):
  try: RefreshToken(request.data['refresh']).blacklist(); return Response(status=205)
  except Exception: return Response({'detail':'Invalid refresh token.'},status=400)
class ChangePasswordView(APIView):
 permission_classes=[OwnerOnly]
 def post(self,request):
  if not request.user.check_password(request.data.get('old_password','')): return Response({'old_password':'Incorrect password.'},status=400)
  request.user.set_password(request.data.get('new_password','')); request.user.save(); return Response({'detail':'Password changed.'})
class BaseViewSet(viewsets.ModelViewSet):
 permission_classes=[IsOwnerOrReadOnly]
class ProfileViewSet(BaseViewSet):
 queryset=Profile.objects.all(); serializer_class=PublicProfileSerializer; http_method_names=['get','patch','head','options']
 def get_serializer_class(self):
  if self.request.user.is_authenticated and self.request.user.is_superuser:
   return OwnerProfileSerializer
  return PublicProfileSerializer
 def list(self,request,*a,**kw):
  obj=Profile.objects.first()
  return Response(self.get_serializer(obj).data if obj else {})
 def retrieve(self,request,*a,**kw): return self.list(request,*a,**kw)
 def partial_update_singleton(self,request,*a,**kw):
  obj=Profile.objects.first()
  if obj is None: return Response({'detail':'Profile not found.'},status=status.HTTP_404_NOT_FOUND)
  serializer=self.get_serializer(obj,data=request.data,partial=True)
  serializer.is_valid(raise_exception=True)
  serializer.save()
  return Response(serializer.data)
class SkillViewSet(BaseViewSet):
 queryset=Skill.objects.all(); serializer_class=SkillSerializer; filterset_fields=['category','is_featured']; search_fields=['name']; ordering_fields=['display_order','proficiency']; ordering=['display_order','pk']
class ExperienceViewSet(BaseViewSet):
 queryset=Experience.objects.all(); serializer_class=ExperienceSerializer; search_fields=['company','role','description']; ordering_fields=['start_date','company','role']; ordering=['-start_date','pk']
class EducationViewSet(BaseViewSet):
 queryset=Education.objects.all(); serializer_class=EducationSerializer; search_fields=['institution','degree','field_of_study']; ordering_fields=['start_year','end_year','institution']; ordering=['-start_year','pk']
class ProjectViewSet(BaseViewSet):
 queryset=Project.objects.all(); serializer_class=ProjectSerializer; lookup_field='slug'; filterset_fields=['category','is_featured']; search_fields=['title','summary','description']; ordering_fields=['completed_date','display_order']; ordering=['display_order','pk']; pagination_class=type('ProjectPagination',( __import__('rest_framework.pagination',fromlist=['PageNumberPagination']).PageNumberPagination,),{'page_size':9})
class CategoryViewSet(BaseViewSet):
 queryset=Category.objects.all(); serializer_class=CategorySerializer; search_fields=['name','description']; ordering_fields=['name','created_at']; ordering=['name','pk']
class TagViewSet(BaseViewSet):
 queryset=Tag.objects.all(); serializer_class=TagSerializer; search_fields=['name']; ordering_fields=['name','created_at']; ordering=['name','pk']
class PostViewSet(BaseViewSet):
 serializer_class=PostSerializer; lookup_field='slug'; filterset_fields=['category__slug','tags__slug','is_featured']; search_fields=['title','excerpt','content']; ordering_fields=['published_at','views_count','title']; ordering=['-published_at','pk']
 def get_queryset(self):
  qs=Post.objects.annotate(likes_count=Count('likes',distinct=True),comments_count=Count('comments',filter=__import__('django.db.models',fromlist=['Q']).Q(comments__is_approved=True),distinct=True)).prefetch_related('tags')
  if not (self.request.user.is_authenticated and self.request.user.is_superuser): return qs.filter(status='PUBLISHED')
  state=self.request.query_params.get('status')
  if state=='DRAFT': return qs.filter(status='DRAFT')
  if state=='all': return qs
  return qs.filter(status='PUBLISHED')
 def retrieve(self,request,*a,**kw):
  response=super().retrieve(request,*a,**kw); visitor=request.headers.get('X-Visitor-Id')
  if visitor:
   key=f'post-view:{response.data["slug"]}:{visitor}'
   from django.core.cache import cache
   if not cache.get(key): Post.objects.filter(slug=kw['slug']).update(views_count=F('views_count')+1); cache.set(key,True,timeout=86400); response.data['views_count']+=1
  return response
 def perform_create(self,serializer): serializer.save(author=self.request.user)
 @action(detail=True,methods=['post'],permission_classes=[AllowAny],throttle_classes=[LikeThrottle])
 def like(self,request,slug=None):
  visitor=request.headers.get('X-Visitor-Id')
  if not visitor: return Response({'detail':'X-Visitor-Id header required.'},status=400)
  post=self.get_object(); like,created=PostLike.objects.get_or_create(post=post,visitor_id=visitor,defaults={'ip_address':request.META.get('REMOTE_ADDR')})
  if not created: like.delete()
  return Response({'liked':created,'likes_count':post.likes.count()})
 @action(detail=True,methods=['get','post'],url_path='comments',permission_classes=[AllowAny])
 def comments(self,request,slug=None):
  post=self.get_object()
  if request.method=='GET':
   roots=Comment.objects.filter(post=post,is_approved=True,parent__isnull=True).order_by('-created_at')
   return Response([{'id':c.id,'name':c.name,'content':c.content,'created_at':c.created_at,'replies':[{'id':r.id,'name':r.name,'content':r.content,'created_at':r.created_at} for r in c.replies.filter(is_approved=True)]} for c in roots])
  throttle=CommentThrottle()
  if not throttle.allow_request(request,self):
   raise Throttled(wait=throttle.wait())
  s=CommentSerializer(
   data=request.data,
   context={**self.get_serializer_context(),'post':post},
  )
  s.is_valid(raise_exception=True); s.save(post=post); return Response({'detail':'Your comment is awaiting approval.'},status=201)
class CommentModerationViewSet(BaseViewSet):
 queryset=Comment.objects.all(); serializer_class=OwnerCommentSerializer; permission_classes=[OwnerOnly]; filterset_fields=['is_approved','post__slug']; search_fields=['name','email','content']; ordering_fields=['created_at','name']; ordering=['-created_at','pk']
 @action(detail=True,methods=['post'],serializer_class=CommentApprovalSerializer)
 def approval(self,request,pk=None):
  comment=self.get_object()
  serializer=self.get_serializer(data=request.data)
  serializer.is_valid(raise_exception=True)
  comment.is_approved=serializer.validated_data['is_approved']
  comment.save(update_fields=['is_approved'])
  return Response(OwnerCommentSerializer(comment,context=self.get_serializer_context()).data)
class CommentReplyCreateView(APIView):
 permission_classes=[OwnerOnly]
 def post(self,request):
  serializer=CommentReplyCreateSerializer(data=request.data)
  serializer.is_valid(raise_exception=True)
  reply=serializer.save()
  return Response(OwnerCommentSerializer(reply,context={'request':request}).data,status=status.HTTP_201_CREATED)
class ContactViewSet(BaseViewSet):
 queryset=ContactMessage.objects.all(); serializer_class=ContactSerializer; permission_classes=[ContactMessagePermission]; filterset_fields=['is_read']; search_fields=['name','email','subject','message']; ordering_fields=['created_at','name','subject']; ordering=['-created_at','pk']; pagination_class=type('MessagePagination',(__import__('rest_framework.pagination',fromlist=['PageNumberPagination']).PageNumberPagination,),{'page_size':10})
 def get_throttles(self): return [ContactThrottle()] if self.request.method=='POST' else []
 def get_queryset(self): return ContactMessage.objects.all() if self.request.user.is_authenticated and self.request.user.is_superuser else ContactMessage.objects.none()
 def get_serializer_class(self):
  if getattr(self,'action',None)=='read_state':
   return ContactReadStateSerializer
  return ContactSerializer
 @action(detail=True,methods=['patch'],permission_classes=[OwnerOnly],serializer_class=ContactReadStateSerializer,url_path='read-state')
 def read_state(self,request,pk=None):
  message=self.get_object()
  serializer=self.get_serializer(message,data=request.data,partial=False)
  serializer.is_valid(raise_exception=True)
  serializer.save()
  return Response(serializer.data)
class DashboardStatsView(APIView):
 permission_classes=[OwnerOnly]
 def get(self,request):
  from django.db.models.functions import TruncMonth
  posts=Post.objects.all(); months=posts.filter(created_at__gte=timezone.now()-timedelta(days=183)).annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month')
  return Response({'total_posts':posts.count(),'published_posts':posts.filter(status='PUBLISHED').count(),'draft_posts':posts.filter(status='DRAFT').count(),'total_projects':Project.objects.count(),'total_skills':Skill.objects.count(),'total_comments':Comment.objects.count(),'pending_comments':Comment.objects.filter(is_approved=False).count(),'total_likes':PostLike.objects.count(),'total_views':posts.aggregate(v=Sum('views_count'))['v'] or 0,'unread_messages':ContactMessage.objects.filter(is_read=False).count(),'top_posts':list(posts.order_by('-views_count').values('title','slug','views_count')[:5]),'recent_comments':list(Comment.objects.order_by('-created_at').values('name','content','created_at')[:5]),'recent_contact_messages':list(ContactMessage.objects.order_by('-created_at').values('id','subject','is_read','created_at')[:5]),'posts_per_month':list(months)})
