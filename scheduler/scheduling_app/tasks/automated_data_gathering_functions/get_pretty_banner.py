def get_pretty_banner(message: str):
    message_length = len(message)
    banner_width = message_length + 8
    return (
        "\n\n"
        + "=" * banner_width
        + "\n"
        + f"=== {message} ===\n"
        + "=" * banner_width
        + "\n"
    )
