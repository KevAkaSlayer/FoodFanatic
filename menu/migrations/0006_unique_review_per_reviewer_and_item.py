from django.db import migrations, models


def remove_duplicate_reviews(apps, schema_editor):
    """Keep the newest review per (reviewer, item) before the constraint lands."""
    Review = apps.get_model("menu", "Review")

    newest_by_key = {}
    stale_ids = []
    # Oldest first, so the last row seen for a key is the one that survives.
    for review in Review.objects.order_by("created", "pk").iterator():
        key = (review.reviewer_id, review.item_id)
        if key in newest_by_key:
            stale_ids.append(newest_by_key[key])
        newest_by_key[key] = review.pk

    if stale_ids:
        Review.objects.filter(pk__in=stale_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0005_phase1_integrity"),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_reviews,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(
                fields=("reviewer", "item"),
                name="unique_review_per_reviewer_and_item",
            ),
        ),
    ]
