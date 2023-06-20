# Generated by Django 3.2 on 2023-01-20 14:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("motioneye", "0004_alter_motioneyevariable_service"),
    ]

    operations = [
        migrations.AlterField(
            model_name="motioneyevariable",
            name="service",
            field=models.CharField(
                choices=[
                    ("snapshot", "Snapshot"),
                    ("lock", "Lock"),
                    ("unlock", "Unlock"),
                    ("light_on", "Light on"),
                    ("light_off", "Light off"),
                    ("alarm_on", "Alarm on"),
                    ("alarm_off", "Alarm off"),
                    ("up", "Up"),
                    ("right", "Right"),
                    ("down", "Down"),
                    ("left", "Left"),
                    ("zoom_in", "Zoom in"),
                    ("zoom_out", "Zoom out"),
                    ("preset1", "Preset1"),
                    ("preset2", "Preset2"),
                    ("preset3", "Preset3"),
                    ("preset4", "Preset4"),
                    ("preset5", "Preset5"),
                    ("preset6", "Preset6"),
                    ("preset7", "Preset7"),
                    ("preset8", "Preset8"),
                    ("preset9", "Preset9"),
                    ("record_start", "Record start"),
                    ("record_stop", "Record stop"),
                    ("left_text", "Left text overlay"),
                    ("right_text", "Right text overlay"),
                    ("movies", "Movie state"),
                    ("enabled", "Device state"),
                    ("recording_mode", "Recording mode"),
                ],
                default="snapshot",
                help_text="Action to send or text overlay to write over the image/video",
                max_length=50,
            ),
        ),
    ]
