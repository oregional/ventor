/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { AttachmentList } from "@mail/core/common/attachment_list";

patch(AttachmentList.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
    },

    canPrint() {
        return session.dpc_company_enabled && session.dpc_user_enabled;
    },

    getActions(attachment) {
        const actions = super.getActions(attachment);

        if (!this.canPrint() || !attachment || attachment.uploading || attachment.type === "url") {
            return actions;
        }

        const printAction = {
            label: _t("Print"),
            icon: "fa fa-print",
            onSelect: () => this.onClickPrint(attachment),
        };

        const downloadIndex = actions.findIndex(({ label }) => label === _t("Download"));
        const insertIndex = downloadIndex >= 0 ? downloadIndex + 1 : actions.length;

        actions.splice(insertIndex, 0, printAction);

        return actions;
    },

    async onClickPrint(attachment) {
        try {
            const [message] = await this.orm.call(
                "ir.attachment",
                "dpc_print",
                [[attachment.id]]
            );

            this.notification.add(message, {
                type: "success",
            });
        } catch {
            const fileName = attachment.name || "Document";

            this.notification.add(`Failed to print "${fileName}". Please make sure that printers are
                selected at the user or company level.`, {
                type: "danger",
            });
        }
    },
});
