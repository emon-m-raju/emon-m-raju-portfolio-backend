from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
class AbsoluteURLMixin:
 def to_representation(self,instance):
  data=super().to_representation(instance); request=self.context.get('request')
  for field in ['avatar','resume','cover_image']:
   if not data.get(field): continue
   if field=='avatar' and isinstance(instance,Profile) and instance.avatar.name=='profile.jpg':
    data[field]='/profile.jpg'
   elif request:
    data[field]=request.build_absolute_uri(data[field])
  return data
class ProfileSerializer(AbsoluteURLMixin,serializers.ModelSerializer):
 class Meta: model=Profile; fields='__all__'
class PublicProfileSerializer(AbsoluteURLMixin,serializers.ModelSerializer):
 class Meta:
  model=Profile
  fields=['id','full_name','headline','bio','location','avatar','github_url','linkedin_url','x_url','website_url','years_of_experience','is_available_for_hire']
class OwnerProfileSerializer(ProfileSerializer):
 class Meta(ProfileSerializer.Meta):
  fields='__all__'
class SkillSerializer(serializers.ModelSerializer):
 proficiency=serializers.IntegerField(min_value=1,max_value=100)
 class Meta: model=Skill; fields='__all__'
class ExperienceSerializer(serializers.ModelSerializer):
 def validate(self,d):
  start=d.get('start_date',getattr(self.instance,'start_date',None)); end=d.get('end_date',getattr(self.instance,'end_date',None)); current=d.get('is_current',getattr(self.instance,'is_current',False))
  from django.utils import timezone
  if start and start>timezone.localdate(): raise serializers.ValidationError({'start_date':'Start date cannot be in the future.'})
  if current and end: raise serializers.ValidationError({'end_date':'End date must be empty for a current role.'})
  if not current and (not end or (start and end<=start)): raise serializers.ValidationError({'end_date':'End date must be after start date.'})
  return d
 class Meta: model=Experience; fields='__all__'
class EducationSerializer(serializers.ModelSerializer):
 def validate(self,d):
  start=d.get('start_year',getattr(self.instance,'start_year',None)); end=d.get('end_year',getattr(self.instance,'end_year',None))
  if start and end and end<start: raise serializers.ValidationError({'end_year':'End year cannot be earlier than start year.'})
  return d
 class Meta: model=Education; fields='__all__'
class ProjectSerializer(AbsoluteURLMixin,serializers.ModelSerializer):
 def validate(self,d):
  if not (d.get('live_url',getattr(self.instance,'live_url','')) or d.get('github_url',getattr(self.instance,'github_url',''))): raise serializers.ValidationError('At least one of live_url or github_url is required.')
  return d
 class Meta: model=Project; fields='__all__'
class CategorySerializer(serializers.ModelSerializer):
 posts_count=serializers.SerializerMethodField()
 def get_posts_count(self,obj): return obj.posts.filter(status='PUBLISHED').count()
 class Meta: model=Category; fields='__all__'
class TagSerializer(serializers.ModelSerializer):
 posts_count=serializers.SerializerMethodField()
 def get_posts_count(self,obj): return obj.post_set.filter(status='PUBLISHED').count()
 class Meta: model=Tag; fields='__all__'
class CommentSerializer(serializers.ModelSerializer):
 email=serializers.EmailField(write_only=True)
 class Meta: model=Comment; fields='__all__'; read_only_fields=['is_approved','created_at','post']
 def validate(self,data):
  parent=data.get('parent')
  if parent:
   if parent.parent_id is not None:
    raise serializers.ValidationError({'parent':'Replies must be attached to a top-level comment.'})
   post=self.context.get('post')
   if post is None or parent.post_id!=post.pk:
    raise serializers.ValidationError({'parent':'The parent comment must belong to this post.'})
  return data
 def validate_content(self,v):
  if not 5<=len(v)<=1000: raise serializers.ValidationError('Content must be 5–1000 characters.')
  return v
class OwnerCommentSerializer(serializers.ModelSerializer):
 class Meta: model=Comment; fields='__all__'
class CommentApprovalSerializer(serializers.Serializer):
 is_approved=serializers.BooleanField()
class CommentReplyCreateSerializer(serializers.ModelSerializer):
 post=serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
 parent=serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all())
 class Meta:
  model=Comment
  fields=['post','parent','name','email','website','content']
 def validate_content(self,v):
  if not 5<=len(v)<=1000: raise serializers.ValidationError('Content must be 5–1000 characters.')
  return v
 def validate(self,data):
  parent=data['parent']
  if parent.parent_id is not None:
   raise serializers.ValidationError({'parent':'Replies must be attached to a top-level comment.'})
  if parent.post_id!=data['post'].pk:
   raise serializers.ValidationError({'post':'The parent comment and reply must belong to the same post.'})
  return data
 def create(self,validated_data):
  return Comment.objects.create(**validated_data,is_approved=True)
class PostSerializer(AbsoluteURLMixin,serializers.ModelSerializer):
 likes_count=serializers.IntegerField(read_only=True); comments_count=serializers.IntegerField(read_only=True)
 class Meta: model=Post; fields='__all__'; read_only_fields=['author','published_at','views_count','reading_time']
 def validate_title(self,v):
  if len(v)<5: raise serializers.ValidationError('Title must be at least 5 characters.')
  return v
 def validate(self,d):
  status=d.get('status',getattr(self.instance,'status','DRAFT')); content=d.get('content',getattr(self.instance,'content','')); category=d.get('category',getattr(self.instance,'category',None))
  if status=='PUBLISHED' and len(content.split())<300: raise serializers.ValidationError({'content':'Published posts need at least 300 words.'})
  if status=='PUBLISHED' and not category: raise serializers.ValidationError({'category':'Published posts need a category.'})
  return d
class ContactSerializer(serializers.ModelSerializer):
 class Meta: model=ContactMessage; fields='__all__'; read_only_fields=['is_read','created_at']
 def validate_message(self,v):
  if not 10<=len(v)<=2000: raise serializers.ValidationError('Message must be 10–2000 characters.')
  return v
class ContactReadStateSerializer(serializers.ModelSerializer):
 class Meta: model=ContactMessage; fields=['is_read']
