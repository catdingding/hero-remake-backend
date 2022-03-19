import sys
import django

sys.path.insert(0, "/app")
django.setup()

from system.utils import send_system_message

sender_name, avatar_id, content = sys.argv[1:4]

send_system_message(sender_name, int(avatar_id), content)
