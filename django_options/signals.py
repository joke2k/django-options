import django.dispatch

option_value_changed = django.dispatch.Signal(providing_args=["old_value","new_value","option"])

