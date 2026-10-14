"""Phone state listener for incoming voice and video calls."""

from analyzer import analyzer as az
import trust

try:
    from jnius import autoclass, PythonJavaClass, java_method, cast
    from android import mActivity
    ANDROID = True
except Exception:
    ANDROID = False


def _notify(title, summary, detail):
    try:
        from notifier import notify
        notify(title, summary, detail)
    except Exception as e:
        print("[call notifier]", e)


def analyze_call(number, kind="voice"):
    entry = trust.record(number, known=False)
    result = az.analyze_call({
        "number": number,
        "recent_calls_last_hour": entry["count"],
        "avg_duration_seconds": 5,
        "duration_seconds": 5,
        "caller_spoke_first": True,
    })
    trusted = trust.is_trusted(number)
    if not trusted and result["verdict"] in ("suspicious", "phishing"):
        label = "Video call" if kind == "video" else "Call"
        _notify(
            "%s from untrusted number" % label,
            "From %s - score %d/100" % (number, result["score"]),
            "Do not answer or share info. Open AntiPhish for details.",
        )
    return result


if ANDROID:
    class PhoneStateReceiver(PythonJavaClass):
        __javainterfaces__ = ["android/telephony/PhoneStateListener"]
        __javacontext__ = "app"

        @java_method("(I)V")
        def onCallStateChanged(self, state):
            try:
                TelephonyManager = autoclass("android.telephony.TelephonyManager")
                if state == TelephonyManager.CALL_STATE_RINGING:
                    number = "(unknown caller)"
                    analyze_call(number, kind="voice")
            except Exception as e:
                print("PhoneStateReceiver error:", e)

    def register_phone_listener():
        try:
            TelephonyManager = autoclass("android.telephony.TelephonyManager")
            context = mActivity.getApplicationContext()
            tm = cast(TelephonyManager, context.getSystemService("phone"))
            listener = PhoneStateReceiver()
            tm.listen(listener, 1)  # LISTEN_CALL_STATE
            print("Phone listener registered")
            return listener
        except Exception as e:
            print("register_phone_listener failed:", e)
            return None
else:
    def register_phone_listener():
        print("Desktop mode - phone listener not available")
        return None
