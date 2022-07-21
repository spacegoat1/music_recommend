from django.db import migrations
from django.contrib.auth.models import User

def forwards_func(apps, schema_editor):

    user = User.objects.create_user('user1', 'user1@user.com', 'admin')

class Migration(migrations.Migration):

    dependencies = [
        ('mr', '0005_populate_trackweight'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]