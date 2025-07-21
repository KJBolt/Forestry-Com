/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { useState } from "@odoo/owl";

export class CustomImportButton extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.state = useState({
            currentModel: this.env.searchModel?.resModel || ''
        });
        
        // Update state when model changes
        this.env.bus.addEventListener('RPC:RESPONSE', () => {
            const newModel = this.env.searchModel?.resModel || '';
            if (newModel !== this.state.currentModel) {
                this.state.currentModel = newModel;
                console.log('currentModel', this.state.currentModel);
            }
        });
    }

    onClick() {
        // Define the action to open the import wizard
        const action = {
            type: 'ir.actions.act_window',
            name: 'Import Trees',
            res_model: 'forest.tree.import.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
        };

        // Open the import wizard
        this.actionService.doAction(action);
    }
}

// Register the component
const viewsCategory = registry.category("views")
export const cImportButton = {
    ...listView,
    Controller: CustomImportButton,
}

viewsCategory.add("custom_import_button", cImportButton);
