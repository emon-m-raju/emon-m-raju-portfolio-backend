from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portfolio.models import Comment, Post


DEMO_COMMENTS = (
    {
        'name': 'Demo Visitor 1',
        'email': 'demo-visitor-1@example.invalid',
        'content': '[DEMO COMMENT] Fictional sample feedback 1: This comment exists only to demonstrate the owner moderation interface.',
        'approved': True,
        'post_index': 0,
    },
    {
        'name': 'Demo Visitor 2',
        'email': 'demo-visitor-2@example.invalid',
        'content': '[DEMO COMMENT] Fictional sample feedback 2: This comment exists only to demonstrate the owner moderation interface.',
        'approved': True,
        'post_index': 1,
    },
    {
        'name': 'Demo Visitor 3',
        'email': 'demo-visitor-3@example.invalid',
        'content': '[DEMO COMMENT] Fictional sample feedback 3: This comment exists only to demonstrate the owner moderation interface.',
        'approved': True,
        'post_index': 2,
    },
    {
        'name': 'Demo Visitor 4',
        'email': 'demo-visitor-4@example.invalid',
        'content': '[DEMO COMMENT] Fictional sample feedback 4: This comment exists only to demonstrate the owner moderation interface.',
        'approved': False,
        'post_index': 3,
    },
    {
        'name': 'Demo Visitor 5',
        'email': 'demo-visitor-5@example.invalid',
        'content': '[DEMO COMMENT] Fictional sample feedback 5: This comment exists only to demonstrate the owner moderation interface.',
        'approved': False,
        'post_index': 0,
    },
)

DEMO_REPLY = {
    'name': 'Demo Portfolio Owner',
    'email': 'demo-owner@example.invalid',
    'content': '[DEMO COMMENT] Fictional owner reply: This reply demonstrates the threaded comment interface and is not a real visitor exchange.',
}


class Command(BaseCommand):
    help = 'Safely preview or create clearly labeled demo comments; defaults to dry-run.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write missing demo comments after reviewing the dry-run output.',
        )

    def handle(self, *args, **options):
        posts = list(
            Post.objects.filter(status='PUBLISHED').order_by('pk')
        )
        if len(posts) < 4:
            raise CommandError(
                'At least four existing published posts are required; no records were changed.'
            )

        definitions = list(DEMO_COMMENTS)
        definitions.append({
            **DEMO_REPLY,
            'approved': True,
            'post_index': 0,
            'parent_content': DEMO_COMMENTS[0]['content'],
        })
        existing = {}
        for comment in Comment.objects.filter(
            content__in=[entry['content'] for entry in definitions]
        ).select_related('post', 'parent'):
            if comment.content in existing:
                raise CommandError(
                    f'Multiple rows already use demo content {comment.content!r}; '
                    'no records were changed.'
                )
            existing[comment.content] = comment

        roots_to_create = []
        planned = []
        for entry in DEMO_COMMENTS:
            post = posts[entry['post_index']]
            comment = existing.get(entry['content'])
            if comment:
                self._validate_existing(comment, entry, post, None)
            else:
                roots_to_create.append(Comment(
                    post=post,
                    name=entry['name'],
                    email=entry['email'],
                    content=entry['content'],
                    is_approved=entry['approved'],
                ))
            planned.append((entry, post, comment))

        reply_entry = definitions[-1]
        reply_post = posts[reply_entry['post_index']]
        reply = existing.get(reply_entry['content'])
        parent = existing.get(reply_entry['parent_content'])
        if reply:
            if parent is None:
                parent = Comment.objects.filter(
                    content=reply_entry['parent_content']
                ).first()
            self._validate_existing(reply, reply_entry, reply_post, parent)

        self.stdout.write('Demo comment seed preview (no existing records will be altered):')
        for entry, post, comment in planned:
            action = 'already present' if comment else 'CREATE'
            state = 'approved' if entry['approved'] else 'pending'
            self.stdout.write(
                f"  {action}: {entry['name']} <{entry['email']}> | "
                f"{state} | post: {post.title} | {entry['content']}"
            )
        reply_action = 'already present' if reply else 'CREATE'
        self.stdout.write(
            f"  {reply_action}: {reply_entry['name']} <{reply_entry['email']}> | "
            f"approved reply to {DEMO_COMMENTS[0]['name']} | post: {reply_post.title} | "
            f"{reply_entry['content']}"
        )

        if not options['apply']:
            self.stdout.write(
                self.style.WARNING('Dry run only. No database rows were written. '
                                   'Pass --apply only after reviewing and approving this exact content.')
            )
            return

        with transaction.atomic():
            if roots_to_create:
                Comment.objects.bulk_create(roots_to_create)

            if not reply:
                parent = Comment.objects.get(content=DEMO_COMMENTS[0]['content'])
                Comment.objects.bulk_create([Comment(
                    post=reply_post,
                    parent=parent,
                    name=reply_entry['name'],
                    email=reply_entry['email'],
                    content=reply_entry['content'],
                    is_approved=reply_entry['approved'],
                )])

        self.stdout.write(self.style.SUCCESS('Missing demo comments created; existing records were left unchanged.'))

    @staticmethod
    def _validate_existing(comment, entry, post, parent):
        expected = (
            comment.name == entry['name']
            and comment.email == entry['email']
            and comment.post_id == post.pk
            and comment.is_approved == entry['approved']
            and comment.parent_id == (parent.pk if parent else None)
        )
        if not expected:
            raise CommandError(
                f'Existing row conflicts with demo seed content {entry["content"]!r}; '
                'no records were changed.'
            )
