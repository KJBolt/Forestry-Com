/** @odoo-module **/

import {many2OneField} from "@web/views/fields/many2one/many2one_field";
import {patch} from "@web/core/utils/patch";

const patchDescr = () => ({
    extractProps(fieldInfo) {
        const options = fieldInfo.options || {};

        // no create
        if (options.no_create === undefined) {
            options.no_create = true
        }

        // can quick create
        if (options.no_quick_create === undefined) {
            options.no_quick_create = true
        }

        // no create/edit
        if (options.no_create_edit === undefined) {
            options.no_create_edit = true
        }

        return super.extractProps(...arguments);
    },
});

patch(many2OneField, patchDescr());
