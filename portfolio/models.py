import uuid, os
from django.db import models, router
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class TimeStamped(models.Model):
 created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 class Meta: abstract=True
class Profile(TimeStamped):
 full_name=models.CharField(max_length=160); headline=models.CharField(max_length=200); bio=models.TextField(); email=models.EmailField(); phone=models.CharField(max_length=30,blank=True); location=models.CharField(max_length=120,blank=True); avatar=models.ImageField(upload_to='profile/',blank=True,null=True); resume=models.FileField(upload_to='resume/',blank=True,null=True); github_url=models.URLField(blank=True); linkedin_url=models.URLField(blank=True); x_url=models.URLField(blank=True); website_url=models.URLField(blank=True); years_of_experience=models.PositiveIntegerField(default=0); is_available_for_hire=models.BooleanField(default=False)
 class Meta:
  constraints=[models.CheckConstraint(condition=models.Q(pk=1),name='profile_singleton_pk')]
 def save(self,*a,**kw):
  self.pk=1
  using=kw.get('using') or router.db_for_write(type(self),instance=self)
  if self._state.adding:
   existing=Profile.objects.using(using).filter(pk=1).only('created_at').first()
   if existing:
    self.created_at=existing.created_at
    self._state.adding=False
    kw.pop('force_insert',None)
  super().save(*a,**kw)
 def __str__(self): return self.full_name
class Skill(TimeStamped):
 CATEGORIES=[(x,x.replace('_',' ').title()) for x in ['FRONTEND','BACKEND','DATABASE','DEVOPS','TOOLS','SOFT_SKILL']]
 name=models.CharField(max_length=80,unique=True); category=models.CharField(max_length=20,choices=CATEGORIES); proficiency=models.PositiveSmallIntegerField(default=50); icon=models.CharField(max_length=80,blank=True); display_order=models.IntegerField(default=0); is_featured=models.BooleanField(default=False)
 def __str__(self): return self.name
class Experience(TimeStamped):
 TYPES=[(x,x.replace('_',' ').title()) for x in ['FULL_TIME','PART_TIME','INTERNSHIP','FREELANCE','CONTRACT']]
 company=models.CharField(max_length=160); role=models.CharField(max_length=160); employment_type=models.CharField(max_length=20,choices=TYPES); location=models.CharField(max_length=120,blank=True); start_date=models.DateField(); end_date=models.DateField(null=True,blank=True); is_current=models.BooleanField(default=False); description=models.TextField(); company_url=models.URLField(blank=True); display_order=models.IntegerField(default=0)
 class Meta: ordering=['-start_date']
class Education(TimeStamped):
 institution=models.CharField(max_length=180); degree=models.CharField(max_length=120); field_of_study=models.CharField(max_length=120); start_year=models.PositiveIntegerField(); end_year=models.PositiveIntegerField(null=True,blank=True); grade=models.CharField(max_length=40,blank=True); description=models.TextField(blank=True)
class Project(TimeStamped):
 CATEGORIES=[(x,x) for x in ['WEB','MOBILE','API','ML','OTHER']]
 title=models.CharField(max_length=180,unique=True); slug=models.SlugField(unique=True,blank=True); summary=models.CharField(max_length=200); description=models.TextField(); cover_image=models.ImageField(upload_to='projects/',blank=True,null=True); tech_stack=models.ManyToManyField(Skill,blank=True); category=models.CharField(max_length=10,choices=CATEGORIES); live_url=models.URLField(blank=True); github_url=models.URLField(blank=True); is_featured=models.BooleanField(default=False); completed_date=models.DateField(null=True,blank=True); display_order=models.IntegerField(default=0)
 def save(self,*a,**kw):
  if not self.slug: self.slug=slugify(self.title)
  super().save(*a,**kw)
class Category(TimeStamped):
 name=models.CharField(max_length=80,unique=True); slug=models.SlugField(unique=True); description=models.TextField(blank=True)
 def __str__(self): return self.name
class Tag(TimeStamped):
 name=models.CharField(max_length=60,unique=True); slug=models.SlugField(unique=True)
 def __str__(self): return self.name
class Post(TimeStamped):
 STATUS=[('DRAFT','Draft'),('PUBLISHED','Published')]
 title=models.CharField(max_length=200); slug=models.SlugField(unique=True,blank=True); excerpt=models.CharField(max_length=300); content=models.TextField(); cover_image=models.ImageField(upload_to='posts/',blank=True,null=True); category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='posts'); tags=models.ManyToManyField(Tag,blank=True); author=models.ForeignKey(User,on_delete=models.PROTECT); status=models.CharField(max_length=12,choices=STATUS,default='DRAFT'); published_at=models.DateTimeField(null=True,blank=True); views_count=models.PositiveIntegerField(default=0); reading_time=models.PositiveIntegerField(default=1); is_featured=models.BooleanField(default=False)
 class Meta: ordering=['-published_at']
 def save(self,*a,**kw):
  if not self.slug: self.slug=slugify(self.title)
  self.reading_time=max(1,(len(self.content.split())+199)//200)
  old=Post.objects.filter(pk=self.pk).values_list('status',flat=True).first() if self.pk else None
  if self.status=='PUBLISHED' and old!='PUBLISHED' and not self.published_at: self.published_at=timezone.now()
  super().save(*a,**kw)
class PostLike(models.Model):
 post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='likes'); visitor_id=models.CharField(max_length=36); ip_address=models.GenericIPAddressField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: unique_together=[('post','visitor_id')]
class Comment(models.Model):
 post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments'); name=models.CharField(max_length=120); email=models.EmailField(); website=models.URLField(blank=True); content=models.TextField(); parent=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='replies'); is_approved=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
class ContactMessage(models.Model):
 name=models.CharField(max_length=120); email=models.EmailField(); subject=models.CharField(max_length=180); message=models.TextField(); is_read=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
