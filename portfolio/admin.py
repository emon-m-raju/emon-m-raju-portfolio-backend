from django.contrib import admin
from .models import *
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): list_display=['full_name','email','location']; search_fields=['full_name','email']
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin): list_display=['name','category','proficiency','is_featured']; list_filter=['category','is_featured']; search_fields=['name']
@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin): list_display=['company','role','start_date','is_current']; list_filter=['employment_type','is_current']; search_fields=['company','role']
@admin.register(Education)
class EducationAdmin(admin.ModelAdmin): list_display=['institution','degree','start_year','end_year']; search_fields=['institution','degree']
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin): list_display=['title','category','is_featured']; list_filter=['category','is_featured']; search_fields=['title']
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): list_display=['name','slug']; search_fields=['name']
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin): list_display=['name','slug']; search_fields=['name']
@admin.register(Post)
class PostAdmin(admin.ModelAdmin): list_display=['title','status','published_at','views_count']; list_filter=['status','category','is_featured']; search_fields=['title','content']
@admin.register(PostLike)
class LikeAdmin(admin.ModelAdmin): list_display=['post','visitor_id','created_at']; search_fields=['visitor_id']
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin): list_display=['name','post','is_approved','created_at']; list_filter=['is_approved']; search_fields=['name','email','content']
@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin): list_display=['name','email','subject','is_read','created_at']; list_filter=['is_read']; search_fields=['name','email','subject']
