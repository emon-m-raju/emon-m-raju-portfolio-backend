from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Comment
@receiver(post_save,sender=Comment)
def notify_new_comment(sender,instance,created,**kwargs):
 if created:
  send_mail('New comment awaiting approval',f'A new comment was submitted on: {instance.post.title}','noreply@devfolio.local',[instance.post.author.email] if instance.post.author.email else [],fail_silently=True)
