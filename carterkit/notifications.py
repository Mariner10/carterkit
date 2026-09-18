"""Notification actions shared by the HTTP, connected-client, and layout APIs."""


def notification_action(action_id, title, *, callback=None, destructive=False,
                        foreground=False, authentication_required=False,
                        text_input=False, text_input_button_title=None,
                        text_input_placeholder=None):
    """Build a button or inline reply for ``notify(actions=[...])``.

    ``callback(frame)`` receives the flat response, including ``userText`` for
    replies. Callbacks require a running CarterClient/Hub; omit them for HTTP-only
    senders and handle responses in your hub's ``on_notif_action`` handler.
    """
    for key, value, limit in (("id", action_id, 64), ("title", title, 48)):
        if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > limit:
            raise ValueError(f"action {key} must be non-empty and <= {limit} UTF-8 bytes")
    if action_id.startswith("com.apple."):
        raise ValueError("action id is reserved by iOS")
    if callback is not None and not callable(callback):
        raise ValueError("action callback must be callable")
    out = {"id": action_id, "title": title}
    for key, value in (("destructive", destructive), ("foreground", foreground),
                       ("authenticationRequired", authentication_required), ("textInput", text_input)):
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be a bool")
        if value:
            out[key] = value
    for key, value, limit in (("textInputButtonTitle", text_input_button_title, 48),
                               ("textInputPlaceholder", text_input_placeholder, 128)):
        if value is not None:
            if not text_input:
                raise ValueError(f"{key} requires text_input=True")
            if not isinstance(value, str) or len(value.encode("utf-8")) > limit:
                raise ValueError(f"{key} must be <= {limit} UTF-8 bytes")
            out[key] = value
    if callback is not None:
        out["callback"] = callback
    return out
