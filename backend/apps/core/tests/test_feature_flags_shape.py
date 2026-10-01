"""Regression tests for the feature_flags shape fix (list-vs-dict bug).

The gate must: honor the canonical dict {key: bool}; tolerate a legacy list of
enabled keys without crashing; and never lock out a feature that isn't
configured. Pure-Python (feature_is_disabled has no Django deps) so it runs
standalone or under pytest.
"""
from apps.core.permissions import feature_is_disabled


def test_dict_explicit_false_is_disabled():
    assert feature_is_disabled({"talent_pool": False}, "talent_pool") is True


def test_dict_explicit_true_is_enabled():
    assert feature_is_disabled({"talent_pool": True}, "talent_pool") is False


def test_dict_missing_key_is_enabled():
    # Unset feature must NOT be locked out (platform stays usable).
    assert feature_is_disabled({"other": False}, "talent_pool") is False


def test_empty_dict_enables_everything():
    assert feature_is_disabled({}, "talent_pool") is False


def test_none_enables_everything():
    assert feature_is_disabled(None, "talent_pool") is False


def test_legacy_list_allowlist_disables_absent_key():
    # Legacy list = enabled keys; a non-empty list that omits the key disables it.
    assert feature_is_disabled(["smart_search"], "talent_pool") is True


def test_legacy_list_allowlist_enables_present_key():
    assert feature_is_disabled(["talent_pool", "smart_search"], "talent_pool") is False


def test_empty_list_disables_nothing():
    assert feature_is_disabled([], "talent_pool") is False


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
