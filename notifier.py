"""Android notification helper. Falls back to a console print on desktop."""

try:
    from jnius import autoclass, cast
    from android import mActivity
    ANDROID = True
except Exception:
    ANDROID = False


def notify(title, summary, detail):
    if not ANDROID:
        print("[notify] %s - %s - %s" % (title, summary, detail))
        return
    try:
        Context = autoclass("android.content.Context")
        NotificationManager = autoclass("android.app.NotificationManager")
        NotificationChannel = autoclass("android.app.NotificationChannel")
        NotificationBuilder = autoclass("android.app.Notification$Builder")
        Build = autoclass("android.os.Build")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()

        channel_id = "antiphish_alerts"
        if Build.VERSION.SDK_INT >= 26:
            manager = cast(NotificationManager,
                           context.getSystemService(Context.NOTIFICATION_SERVICE))
            channel = NotificationChannel(
                channel_id, "AntiPhish Alerts",
                NotificationManager.IMPORTANCE_HIGH,
            )
            channel.setDescription("Phishing and untrusted-sender alerts")
            manager.createNotificationChannel(channel)

        builder = NotificationBuilder(activity, channel_id)
        builder.setContentTitle(title)
        builder.setContentText(summary)
        try:
            style = autoclass("android.app.Notification$BigTextStyle").newInstance()
            style.bigText(detail)
            builder.setStyle(style)
        except Exception:
            pass
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setAutoCancel(True)
        builder.setPriority(NotificationBuilder.PRIORITY_HIGH)

        manager = cast(NotificationManager,
                       context.getSystemService(Context.NOTIFICATION_SERVICE))
        manager.notify(int(__import__("time").time()) % 100000, builder.build())
    except Exception as e:
        print("notify failed:", e)
