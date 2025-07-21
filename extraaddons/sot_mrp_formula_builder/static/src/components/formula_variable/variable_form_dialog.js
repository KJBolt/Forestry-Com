/** @odoo-module */

import {Dialog} from "@web/core/dialog/dialog";
import {Component} from "@odoo/owl";

export class VariableFormDialog extends Component {
    setup() {
        super.setup();
        this.title = this.props.title;
    }

    _cancel() {
        if (this.props.cancel) {
            this.props.cancel();
        }
        this.props.close();
    }

    _confirm() {
        if (this.props.confirm) {
            this.props.confirm({
                name: $("#variableNameTextInput").val(),
                dataType: $("#dataTypeSelect").val(),
            });
        }
        this.props.close();
    }
}

VariableFormDialog.props = {
    title: {
        validate: (m) => {
            return (
                typeof m === "string" || (typeof m === "object" && typeof m.toString === "function")
            );
        },
    },
    body: Object,
    confirm: {type: Function, optional: true},
    cancel: {type: Function, optional: true},
    close: Function,
};

VariableFormDialog.template = "sot_mrp_formula_builder.NewVariableDialog";
VariableFormDialog.components = {Dialog};
VariableFormDialog.defaultProps = {
    defaultName: "",
};
