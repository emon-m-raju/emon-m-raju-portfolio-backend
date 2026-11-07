from io import StringIO

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    Category,
    Comment,
    ContactMessage,
    Post,
    Profile,
    Project,
    Skill,
)


class OwnerDashboardApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.owner = User.objects.create_superuser(
            username='owner-test',
            email='owner@example.test',
            password='test-password',
        )
        self.member = User.objects.create_user(
            username='member-test',
            email='member@example.test',
            password='test-password',
        )
        self.category = Category.objects.create(
            name='Testing',
            slug='testing',
        )
        self.profile = Profile.objects.create(
            full_name='Portfolio Owner',
            headline='Developer',
            bio='A public biography.',
            email='private@example.test',
            phone='0123456789',
            resume='resume/private.pdf',
            location='Dhaka',
        )
        self.published_post = Post.objects.create(
            title='Published post',
            slug='published-post',
            excerpt='Published excerpt',
            content='Published content.',
            category=self.category,
            author=self.owner,
            status='PUBLISHED',
        )
        self.draft_post = Post.objects.create(
            title='Draft post',
            slug='draft-post',
            excerpt='Draft excerpt',
            content='Draft content.',
            category=self.category,
            author=self.owner,
            status='DRAFT',
        )
        self.pending_comment = Comment.objects.create(
            post=self.published_post,
            name='Visitor',
            email='visitor@example.test',
            content='A comment awaiting review.',
        )
        self.contact_message = ContactMessage.objects.create(
            name='Contact Visitor',
            email='contact@example.test',
            subject='Question',
            message='A private contact message.',
        )

    def authenticate_owner(self):
        self.client.force_authenticate(self.owner)

    def test_profile_public_fields_are_safe_and_owner_can_patch_singleton(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['full_name'], 'Portfolio Owner')
        self.assertNotIn('email', response.data)
        self.assertNotIn('phone', response.data)
        self.assertNotIn('resume', response.data)

        self.client.force_authenticate(self.member)
        denied = self.client.patch('/api/profile/', {'phone': '999'}, format='json')
        self.assertEqual(denied.status_code, 403)

        self.authenticate_owner()
        owner_response = self.client.get('/api/profile/')
        self.assertEqual(owner_response.data['email'], 'private@example.test')
        self.assertEqual(owner_response.data['phone'], '0123456789')
        self.assertIn('resume', owner_response.data)

        patched = self.client.patch(
            '/api/profile/',
            {'phone': '01700000000', 'bio': 'Updated owner bio.'},
            format='json',
        )
        self.assertEqual(patched.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '01700000000')
        self.assertEqual(self.profile.bio, 'Updated owner bio.')

    def test_profile_save_and_database_constraint_enforce_singleton(self):
        Profile.objects.create(
            full_name='Replacement Owner',
            headline='Updated developer',
            bio='Replacement biography.',
            email='replacement@example.test',
        )
        self.assertEqual(Profile.objects.count(), 1)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Replacement Owner')

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Profile.objects.bulk_create([
                    Profile(
                        pk=2,
                        full_name='Second Profile',
                        headline='Developer',
                        bio='A second profile.',
                        email='second@example.test',
                    ),
                ])

    def test_owner_only_comment_approval_and_public_visibility(self):
        approval_url = f'/api/comments/{self.pending_comment.pk}/approval/'
        anonymous = self.client.post(
            approval_url,
            {'is_approved': True},
            format='json',
        )
        self.assertEqual(anonymous.status_code, 401)

        public = self.client.get(
            f'/api/posts/{self.published_post.slug}/comments/',
        )
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.data, [])

        submitted = self.client.post(
            f'/api/posts/{self.published_post.slug}/comments/',
            {
                'name': 'Public Visitor',
                'email': 'public@example.test',
                'content': 'This comment cannot self-approve.',
                'is_approved': True,
            },
            format='json',
        )
        self.assertEqual(submitted.status_code, 201)
        public_comment = Comment.objects.get(name='Public Visitor')
        self.assertFalse(public_comment.is_approved)

        self.authenticate_owner()
        invalid = self.client.post(approval_url, {}, format='json')
        self.assertEqual(invalid.status_code, 400)
        approved = self.client.post(
            approval_url,
            {'is_approved': True},
            format='json',
        )
        self.assertEqual(approved.status_code, 200)
        self.pending_comment.refresh_from_db()
        self.assertTrue(self.pending_comment.is_approved)

        public = self.client.get(
            f'/api/posts/{self.published_post.slug}/comments/',
        )
        self.assertEqual(public.status_code, 200)
        self.assertEqual(len(public.data), 1)
        self.assertNotIn('email', public.data[0])

        rejected = self.client.post(
            approval_url,
            {'is_approved': False},
            format='json',
        )
        self.assertEqual(rejected.status_code, 200)
        self.pending_comment.refresh_from_db()
        self.assertFalse(self.pending_comment.is_approved)

        public = self.client.get(
            f'/api/posts/{self.published_post.slug}/comments/',
        )
        self.assertEqual(public.data, [])

    def test_public_comment_replies_must_be_one_level_and_same_post(self):
        other_post = Post.objects.create(
            title='Different post',
            slug='different-post',
            excerpt='Different excerpt',
            content='Different content.',
            category=self.category,
            author=self.owner,
            status='PUBLISHED',
        )
        other_post_comment = Comment.objects.create(
            post=other_post,
            name='Other visitor',
            email='other@example.test',
            content='A comment on another post.',
        )
        nested_comment = Comment.objects.create(
            post=self.published_post,
            parent=self.pending_comment,
            name='Reply visitor',
            email='reply@example.test',
            content='A reply to the existing comment.',
        )
        url = f'/api/posts/{self.published_post.slug}/comments/'
        payload = {
            'name': 'Reply author',
            'email': 'reply-author@example.test',
            'content': 'This reply must be rejected.',
        }

        cross_post = self.client.post(
            url,
            {**payload, 'parent': other_post_comment.pk},
            format='json',
        )
        self.assertEqual(cross_post.status_code, 400)
        self.assertIn('parent', cross_post.data)

        nested_reply = self.client.post(
            url,
            {**payload, 'parent': nested_comment.pk},
            format='json',
        )
        self.assertEqual(nested_reply.status_code, 400)
        self.assertIn('parent', nested_reply.data)

    def test_public_comment_submission_is_throttled(self):
        url = f'/api/posts/{self.published_post.slug}/comments/'
        payload = {
            'name': 'Frequent visitor',
            'email': 'frequent@example.test',
            'content': 'A comment within the allowed length.',
        }

        responses = [
            self.client.post(url, payload, format='json')
            for _ in range(6)
        ]

        self.assertTrue(all(response.status_code == 201 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)

    def test_owner_reply_must_reference_a_top_level_comment_on_same_post(self):
        other_post = Post.objects.create(
            title='Other post',
            slug='other-post',
            excerpt='Other excerpt',
            content='Other content.',
            category=self.category,
            author=self.owner,
            status='PUBLISHED',
        )
        self.client.force_authenticate(self.member)
        denied = self.client.post(
            '/api/comments/replies/',
            {
                'post': self.published_post.pk,
                'parent': self.pending_comment.pk,
                'name': 'Owner',
                'email': 'owner@example.test',
                'content': 'Owner reply content.',
            },
            format='json',
        )
        self.assertEqual(denied.status_code, 403)

        self.authenticate_owner()
        mismatch = self.client.post(
            '/api/comments/replies/',
            {
                'post': other_post.pk,
                'parent': self.pending_comment.pk,
                'name': 'Owner',
                'email': 'owner@example.test',
                'content': 'Owner reply content.',
            },
            format='json',
        )
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn('post', mismatch.data)

        valid = self.client.post(
            '/api/comments/replies/',
            {
                'post': self.published_post.pk,
                'parent': self.pending_comment.pk,
                'name': 'Owner',
                'email': 'owner@example.test',
                'content': 'Owner reply content.',
            },
            format='json',
        )
        self.assertEqual(valid.status_code, 201)
        self.assertTrue(valid.data['is_approved'])
        self.assertEqual(valid.data['parent'], self.pending_comment.pk)
        self.assertEqual(valid.data['email'], 'owner@example.test')
        nested_reply = self.client.post(
            '/api/comments/replies/',
            {
                'post': self.published_post.pk,
                'parent': valid.data['id'],
                'name': 'Owner',
                'email': 'owner@example.test',
                'content': 'A reply to a reply is not allowed.',
            },
            format='json',
        )
        self.assertEqual(nested_reply.status_code, 400)
        self.assertIn('parent', nested_reply.data)

        public = self.client.get(
            f'/api/posts/{self.published_post.slug}/comments/',
        )
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.data, [])

        self.pending_comment.is_approved = True
        self.pending_comment.save(update_fields=['is_approved'])
        public = self.client.get(
            f'/api/posts/{self.published_post.slug}/comments/',
        )
        self.assertEqual(len(public.data), 1)
        self.assertEqual(len(public.data[0]['replies']), 1)
        self.assertNotIn('email', public.data[0]['replies'][0])

    def test_contact_read_state_is_owner_only_and_public_post_cannot_set_it(self):
        self.assertEqual(self.client.get('/api/contact/').status_code, 401)
        self.assertEqual(
            self.client.get(f'/api/contact/{self.contact_message.pk}/').status_code,
            401,
        )
        denied = self.client.patch(
            f'/api/contact/{self.contact_message.pk}/read-state/',
            {'is_read': True},
            format='json',
        )
        self.assertEqual(denied.status_code, 401)

        submitted = self.client.post(
            '/api/contact/',
            {
                'name': 'New Visitor',
                'email': 'new@example.test',
                'subject': 'New message',
                'message': 'A sufficiently long message.',
                'is_read': True,
            },
            format='json',
        )
        self.assertEqual(submitted.status_code, 201)
        new_message = ContactMessage.objects.get(subject='New message')
        self.assertFalse(new_message.is_read)

        self.authenticate_owner()
        invalid = self.client.patch(
            f'/api/contact/{self.contact_message.pk}/read-state/',
            {'is_read': 'not-a-boolean'},
            format='json',
        )
        self.assertEqual(invalid.status_code, 400)
        updated = self.client.patch(
            f'/api/contact/{self.contact_message.pk}/read-state/',
            {'is_read': True},
            format='json',
        )
        self.assertEqual(updated.status_code, 200)
        self.contact_message.refresh_from_db()
        self.assertTrue(self.contact_message.is_read)

    def test_contact_inbox_is_paginated_filterable_searchable_and_stable(self):
        created = [
            ContactMessage.objects.create(
                name=f'Inbox sender {index}',
                email=f'inbox{index}@example.test',
                subject=f'Inbox subject {index}',
                message=f'Pagination filter target {index}',
                is_read=index % 2 == 0,
            )
            for index in range(10)
        ]
        self.authenticate_owner()

        first_page = self.client.get('/api/contact/')
        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data['count'], 11)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])

        second_page = self.client.get('/api/contact/?page=2')
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.data['results']), 1)

        unread = self.client.get('/api/contact/?is_read=false')
        self.assertEqual(unread.status_code, 200)
        self.assertEqual(unread.data['count'], 6)
        self.assertTrue(all(not message['is_read'] for message in unread.data['results']))

        read = self.client.get('/api/contact/?is_read=true')
        self.assertEqual(read.status_code, 200)
        self.assertEqual(read.data['count'], 5)
        self.assertTrue(all(message['is_read'] for message in read.data['results']))

        searched = self.client.get('/api/contact/?search=filter%20target%209')
        self.assertEqual(searched.status_code, 200)
        self.assertEqual(searched.data['count'], 1)
        self.assertEqual(searched.data['results'][0]['id'], created[-1].id)

    def test_published_posts_require_at_least_300_words(self):
        self.authenticate_owner()
        post_data = {
            'title': 'Assignment word count validation',
            'slug': 'assignment-word-count-validation',
            'excerpt': 'A test of the required published article length.',
            'content': 'sample ' * 299,
            'category': self.category.pk,
            'status': 'PUBLISHED',
            'tags': [],
        }
        too_short = self.client.post('/api/posts/', post_data, format='json')
        self.assertEqual(too_short.status_code, 400)
        self.assertIn('content', too_short.data)

        post_data['content'] = 'sample ' * 300
        long_enough = self.client.post('/api/posts/', post_data, format='json')
        self.assertEqual(long_enough.status_code, 201)
        self.assertEqual(len(long_enough.data['content'].split()), 300)

    def test_demo_comment_seed_defaults_to_read_only_dry_run(self):
        for index in range(3):
            Post.objects.create(
                title=f'Published seed target {index}',
                slug=f'published-seed-target-{index}',
                excerpt='Published test target.',
                content='Published test content.',
                category=self.category,
                author=self.owner,
                status='PUBLISHED',
            )

        initial_count = Comment.objects.count()
        output = StringIO()
        call_command('seed_demo_comments', stdout=output)

        self.assertIn('Dry run only. No database rows were written.', output.getvalue())
        self.assertEqual(Comment.objects.count(), initial_count)

    def test_dashboard_stats_are_owner_only_and_contact_metadata_is_limited(self):
        self.assertEqual(
            self.client.get('/api/dashboard/stats/').status_code,
            401,
        )
        self.authenticate_owner()
        response = self.client.get('/api/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['pending_comments'], 1)
        self.assertEqual(response.data['unread_messages'], 1)
        self.assertEqual(len(response.data['recent_contact_messages']), 1)
        metadata = response.data['recent_contact_messages'][0]
        self.assertEqual(set(metadata), {'id', 'subject', 'is_read', 'created_at'})
        self.assertNotIn('email', metadata)
        self.assertNotIn('message', metadata)
        self.assertNotIn('name', metadata)

    def test_existing_public_and_owner_resource_routes_still_work(self):
        for endpoint in (
            '/api/profile/',
            '/api/skills/',
            '/api/experiences/',
            '/api/education/',
            '/api/projects/',
            '/api/categories/',
            '/api/tags/',
            '/api/posts/',
        ):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(endpoint).status_code, 200)

        public_posts = self.client.get('/api/posts/')
        self.assertEqual(public_posts.status_code, 200)
        self.assertEqual(
            [post['slug'] for post in public_posts.data['results']],
            [self.published_post.slug],
        )

        self.authenticate_owner()
        drafts = self.client.get('/api/posts/?status=DRAFT')
        self.assertEqual(drafts.status_code, 200)
        self.assertEqual(
            [post['slug'] for post in drafts.data['results']],
            [self.draft_post.slug],
        )
        created_skill = self.client.post(
            '/api/skills/',
            {
                'name': 'Test Skill',
                'category': 'BACKEND',
                'proficiency': 50,
            },
            format='json',
        )
        self.assertEqual(created_skill.status_code, 201)
        created_project = self.client.post(
            '/api/projects/',
            {
                'title': 'Regression Project',
                'slug': 'regression-project',
                'summary': 'Regression test project.',
                'description': 'A project used for API regression tests.',
                'category': 'API',
                'github_url': 'https://example.test/project',
            },
            format='json',
        )
        self.assertEqual(created_project.status_code, 201)
