"""Notification listener for voice messages from WhatsApp, Telegram, etc."""

import trust

try:
    from jnius import autoclass, PythonJavaClass, java_method
    from android import mActivity
    ANDROID = True
except Exception:
    ANDROID = False

MESSAGING_PKGS = {
    "com.whatsapp": "WhatsApp",
    "org.telegram.messenger": "Telegram",
    "com.facebook.orca": "Messenger",
    "com.google.android.apps.messaging": "Messages",
    "com.viber.voip": "Viber",
    "com.signal": "Signal",
}

VOICE_HINTS = ["voice message", "voice note", "voice clip", "audio message"]


def _notify(title, summary, detail):
    try:
        from notifier import notify
        notify(title, summary, detail)
    except Exception as e:
        print("[voice notifier]", e)


def analyze_voice_message(sender, body_hint, package):
    entry = trust.record(sender, known=False)
    trusted = trust.is_trusted(sender)
    if not trusted:
        app_name = MESSAGING_PKGS.get(package, package)
        _notify(
            "Voice message from untrusted sender",
            "From %s on %s" % (sender, app_name),
            "Listen carefully. Never share codes or personal info.",
        )
    return {"trusted": trusted, "count": entry["count"]}


if ANDROID:
    class NotifListener(PythonJavaClass):
        __javainterfaces__ = ["android/service/notification/NotificationListenerService"]
        __javacontext__ = "app"

        @java_method("(Landroid/service/notification/StatusBarNotification;)V")
        def onNotificationPosted(self, sbn):
            try:
                package = sbn.getPackageName()
                if package not in MESSAGING_PKGS:
                    return
                notif = sbn.getNotification()
                extras = notif.extras
                title = ""
                text = ""
                if extras:
                    title = extras.getCharSequence("android.title") or ""
                    text = extras.getCharSequence("android.text") or ""
                title = str(title)
                text = str(text)
                combined = (title + " " + text).lower()
                if any(h in combined for h in VOICE_HINTS):
                    analyze_voice_message(title or "(unknown)", text, package)
            except Exception as e:
                print("NotifListener error:", e)

    def register_notif_listener():
        print("Notif listener requires user to enable in Settings > Notification Access")
        return None
else:
    def register_notif_listener():
        print("Desktop mode - notif listener not available")
        return None
