"""Re-encode menu images that were stored before upload compression existed."""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from Food_Fanatic.imaging import compress_image
from menu.models import FoodItem


def megabytes(value):
    return value / (1024 * 1024)


class Command(BaseCommand):
    help = (
        "Downscale menu images already in storage. Each rewritten image is "
        "saved under a new name so cached copies of the original are not served."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the savings without writing anything.",
        )
        parser.add_argument(
            "--max-width",
            type=int,
            default=None,
            help="Override IMAGE_MAX_WIDTH for this run.",
        )
        parser.add_argument(
            "--quality",
            type=int,
            default=None,
            help="Override IMAGE_QUALITY for this run.",
        )
        parser.add_argument(
            "--min-saving",
            type=float,
            default=0.1,
            help=(
                "Only rewrite an image when it gets at least this much smaller "
                "(0.1 means 10%%). Keeps repeat runs from re-encoding images "
                "that are already optimised."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        items = FoodItem.objects.exclude(image="").exclude(image__isnull=True)

        before_total = after_total = 0
        rewritten = skipped = failed = 0

        for item in items.iterator():
            name = item.image.name
            try:
                with item.image.storage.open(name) as stored:
                    original = stored.read()
            except Exception as error:
                failed += 1
                self.stderr.write(f"Could not read {name}: {error}")
                continue

            before_total += len(original)
            compressed = compress_image(
                ContentFile(original),
                max_width=options["max_width"],
                quality=options["quality"],
            )
            saving = (
                0.0
                if compressed is None
                else 1 - compressed.size / max(1, len(original))
            )
            if compressed is None or saving < options["min_saving"]:
                skipped += 1
                after_total += len(original)
                continue

            after_total += compressed.size
            rewritten += 1
            saving *= 100
            self.stdout.write(
                f"{name}: {megabytes(len(original)):.2f} MB -> "
                f"{megabytes(compressed.size):.2f} MB ({saving:.0f}% smaller)"
            )
            if dry_run:
                continue

            # Storage picks a free name, so the public URL changes and no
            # long-lived cache entry can keep serving the original.
            new_name = item.image.storage.save(name, compressed)
            item.image.name = new_name
            item.save(update_fields=("image",))
            if new_name != name:
                try:
                    item.image.storage.delete(name)
                except Exception as error:
                    self.stderr.write(f"Could not delete {name}: {error}")

        summary = (
            f"{rewritten} rewritten, {skipped} already small enough, "
            f"{failed} unreadable: {megabytes(before_total):.1f} MB -> "
            f"{megabytes(after_total):.1f} MB"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run. {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
