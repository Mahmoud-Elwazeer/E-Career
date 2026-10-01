"""Canonicalize SubscriptionPlan.feature_flags to a dict {key: bool}.

The gating logic (check_entitlement 'feature' branch + the only real caller,
employers.TalentPoolViewSet, which checks flags['talent_pool'] is False) and the
existing admin test both use the DICT shape. The model/serializer previously
declared a list. This migration flips the default to dict and normalizes any
existing list rows (a list of ENABLED keys -> {key: True}) so stored data and
code agree. check_entitlement still tolerates stray lists at runtime.
"""
from django.db import migrations, models


def list_to_dict(apps, schema_editor):
    SubscriptionPlan = apps.get_model("core", "SubscriptionPlan")
    for plan in SubscriptionPlan.objects.all():
        flags = plan.feature_flags
        if isinstance(flags, list):
            # Legacy list held the ENABLED feature keys.
            plan.feature_flags = {str(k): True for k in flags}
            plan.save(update_fields=["feature_flags"])
        elif flags is None:
            plan.feature_flags = {}
            plan.save(update_fields=["feature_flags"])


def dict_to_list(apps, schema_editor):
    # Reverse: keep only enabled keys as a list (best-effort).
    SubscriptionPlan = apps.get_model("core", "SubscriptionPlan")
    for plan in SubscriptionPlan.objects.all():
        flags = plan.feature_flags
        if isinstance(flags, dict):
            plan.feature_flags = [k for k, v in flags.items() if v]
            plan.save(update_fields=["feature_flags"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_add_subscription_plan_and_company_subscription"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscriptionplan",
            name="feature_flags",
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text=(
                    "Feature gating map {feature_key: bool}. An explicit False disables "
                    "that feature for the plan; unset keys stay enabled (so new features "
                    "aren't silently locked out). A legacy list of enabled keys is still "
                    "honored for backward compatibility."
                ),
            ),
        ),
        migrations.RunPython(list_to_dict, dict_to_list),
    ]
