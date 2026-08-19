import logging

from odoo import api, SUPERUSER_ID


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # migrate rules
    _migrate_user_rules(env)
    _migrate_report_policies(env)

    # migrate crons
    old_cron_xml_ids = [
        'printnode_base.printnode_limits_update_action',
        'printnode_base.printnode_releases_update_action',
        'printnode_base.printnode_clean_printjob_action',
    ]

    for xml_id in old_cron_xml_ids:
        cron = env.ref(xml_id, raise_if_not_found=False)
        if cron:
            cron.action_archive()

    try:
        with env.cr.savepoint():
            env['printnode.account'].update_subscription_info()
    except Exception as error:
        _logger.exception(
            'Failed to update Direct Print subscription info during migration: %s',
            error,
        )


def _migrate_user_rules(env):
    user_rules = env['printnode.rule'].with_context(
        active_test=False,
    ).search([])

    for user_rule in user_rules:
        env['printnode.print.rule'].create({
            'sequence': 1,
            'active': user_rule.active,
            'user_id': user_rule.user_id.id,
            'report_id': user_rule.report_id.id,
            'printer_id': user_rule.printer_id.id,
            'printer_bin': user_rule.printer_bin.id,
        })

    user_rules.write({
        'active': False,
    })


def _migrate_report_policies(env):
    report_policies = env['printnode.report.policy'].search([
        ('active', '=', True),
    ])

    for report_policy in report_policies:
        # Skip policies that have no printing action.
        if (
            not report_policy.printer_id
            and not report_policy.exclude_from_auto_printing
        ):
            continue

        env['printnode.print.rule'].create({
            'sequence': 2,
            'active': True,
            'report_id': report_policy.report_id.id,
            'printer_id': report_policy.printer_id.id,
            'printer_bin': report_policy.printer_bin.id,
            'report_paper_id': report_policy.report_paper_id.id,
            'exclude_from_auto_printing': report_policy.exclude_from_auto_printing,
        })

    report_policies.write({
        'active': False,
    })
