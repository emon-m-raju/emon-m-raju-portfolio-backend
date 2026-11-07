from django.core.management.base import BaseCommand

from portfolio.models import Category, Profile, Project, Skill


class Command(BaseCommand):
    help = 'Seed the baseline DevFolio demo data.'

    def handle(self, *args, **options):
        profile, _ = Profile.objects.get_or_create(
            pk=1,
            defaults={
                'full_name': 'Md Emon Mahamud Raju',
                'headline': 'Full-Stack Developer (Django & React)',
                'bio': (
                    'Passionate Computer Science student and Full-Stack Developer '
                    'specializing in Django REST Framework, PostgreSQL, and React.'
                ),
                'email': 'emon@example.com',
                'location': 'Dhaka, Bangladesh',
                'years_of_experience': 2,
                'is_available_for_hire': True,
                'github_url': 'https://github.com/emon-m-raju',
                'avatar': 'profile.jpg',
            },
        )
        if profile.avatar.name != 'profile.jpg':
            profile.avatar = 'profile.jpg'
            profile.save(update_fields=['avatar'])

        for name, slug in (
            ('Web Development', 'web-development'),
            ('API & Backend', 'api-backend'),
        ):
            Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )

        skills = (
            ('Python', 'BACKEND', 90),
            ('Django', 'BACKEND', 88),
            ('PostgreSQL', 'DATABASE', 80),
            ('React', 'FRONTEND', 82),
            ('JavaScript', 'FRONTEND', 85),
            ('Git & GitHub', 'TOOLS', 85),
        )
        for name, category, proficiency in skills:
            Skill.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'proficiency': proficiency,
                },
            )

        Project.objects.get_or_create(
            slug='devfolio-portfolio-blog',
            defaults={
                'title': 'DevFolio Portfolio & Blog',
                'summary': (
                    'Full-stack portfolio with Django REST Framework and React.'
                ),
                'description': (
                    'Full-stack portfolio with Django REST Framework and React.'
                ),
                'category': 'WEB',
                'live_url': (
                    'https://emon-m-raju-portfolio-frontend.vercel.app'
                ),
                'is_featured': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('Demo profile, categories, skills, and project are ready.'))
