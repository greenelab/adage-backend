"""
This management command creates or updates a ParticipationType record to
the database. It requires two arguments:
  * name: participation type's name;
  * desc: participation type's description

It can be invoked like this:
  python manage.py create_or_update_participation_type \
--name="High-weight genes" --desc="High-weight genes are ..."
"""

from django.core.management.base import BaseCommand, CommandError
from analyze.models import ParticipationType


class Command(BaseCommand):
    help = "Create or update a participation type in database"

    def add_arguments(self, parser):
        parser.add_argument('--name', dest='name', type=str, required=True)
        parser.add_argument('--desc', dest='desc', type=str, required=True)

    def handle(self, **options):
        try:
            name = options['name'].strip()
            description = options['desc'].strip()
            if not name:
                raise Exception("Participation type's name is blank")
            if not description:
                raise Exception("Participation type's description is blank")

            obj, created = ParticipationType.objects.update_or_create(
                name=name, defaults={'description': description}
            )
            if created:
                action = "created"
            else:
                action = "updated"

            self.stdout.write(
                self.style.SUCCESS(f"Participation type '{name}' {action} successfully")
            )
        except Exception as e:
            raise CommandError("Failed to create or update participation type: %s" % e)
