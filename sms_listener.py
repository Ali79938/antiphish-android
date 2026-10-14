"""SMS listener for Android.
Registers the SMS_RECEIVED receiver, runs the analyzer, and pops a
notification on suspicious or phishing verdicts."""

import os
import trust
from analyzer import analyzer as az

try:
    from jnius import autoclass, PythonJavaClass, java_method
    from android import mActivity
    ANDROID = True
except Exception:
    ANDROID = False


def _log_hit(sender, kind, verdict, score, body):
    path = os.path.join(os.path.expanduser("~"), "antiphish_hits.txt")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("%s|%s|%s|%d|%s\n" % (sender, kind, verdict, score, body[:200]))
    except Exception:
        pass


def _notify(title, summary, detail):
    try:
        from notifier import notify
        notify(title, summary, detail)
    except Exception as e:
        print("[notify]", e)


def analyze_incoming(sender, body):
    trust.record(sender, known=False)
    result = az.analyze_message({"sender": sender, "body": body})
    _log_hit(sender, "sms", result["verdict"], result["score"], body)

    trusted = trust.is_trusted(sender)
    if not trusted and result["verdict"] in ("suspicious", "phishing"):
        _notify(
            "Phishing detected" if result["verdict"] == "phishing" else "Suspicious message",
            "From %s - score %d/100" % (sender, result["score"]),
            "Do not click any links. Open AntiPhish for details.",
        )
    return result


if ANDROID:
    _registered = []

    class SMSReceiver(PythonJavaClass):
        __javainterfaces__ = ["android/content/BroadcastReceiver"]
        __javacontext__ = "app"

        @java_method("(Landroid/content/Context;Landroid/content/Intent;)V")
        def onReceive(self, context, intent):
            try:
                messages = intent.getExtras().get("pdus")
                if not messages:
                    return
                SmsMessage = autoclass("android.telephony.SmsMessage")
                fmt = intent.getExtras().getString("format")
                combined_body = []
                sender = ""
                for pdu in messages:
                    msg = SmsMessage.createFromPdu(pdu, fmt)
                    sender = msg.getDisplayOriginatingAddress() or ""
                    combined_body.append(msg.getMessageBody() or "")
                body = " ".join(combined_body)
                analyze_incoming(sender, body)
            except Exception as e:
                print("SMSReceiver error:", e)

    def register_sms():
        try:
            IntentFilter = autoclass("android.content.IntentFilter")
            context = mActivity.getApplicationContext()
            receiver = SMSReceiver()
            filt = IntentFilter("android.provider.Telephony.SMS_RECEIVED")
            context.registerReceiver(receiver, filt)
            _registered.append(receiver)
            print("SMS receiver registered")
            return receiver
        except Exception as e:
            print("register_sms failed:", e)
            return None

    def stop_all():
        """Unregister all listeners. Called when free session expires."""
        context = mActivity.getApplicationContext()
        for r in _registered:
            try:
                context.unregisterReceiver(r)
            except Exception:
                pass
        _registered.clear()
        print("All listeners stopped")

    def register_all():
        register_sms()
        try:
            from call_listener import register_phone_listener
            register_phone_listener()
        except Exception as e:
            print("phone listener registration failed:", e)
        try:
            from voice_msg_listener import register_notif_listener
            register_notif_listener()
        except Exception as e:
            print("notif listener registration failed:", e)

else:
    def register_sms():
        print("Desktop mode")
        return None

    def register_all():
        print("Desktop mode - no listeners")

    def stop_all():
        print("Desktop mode - nothing to stop")
