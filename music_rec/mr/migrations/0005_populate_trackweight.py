from django.db import migrations


def forwards_func(apps, schema_editor):

    TrackWeight = apps.get_model("mr", "TrackWeight")
    Track = apps.get_model("mr", "Track")

    tracks = Track.objects.all()
    weight = 10000.0
    for t in tracks:
        TrackWeight.objects.create(track=t, weight=weight)


class Migration(migrations.Migration):

    dependencies = [
        ('mr', '0004_INSERT_DATA'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]